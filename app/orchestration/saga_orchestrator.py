import json
import os
import time
from uuid import UUID, uuid4

import psycopg
import pulsar
from psycopg.types.json import Jsonb


WORK_CREATED = "persistent://public/default/hda-work-created-v1"
ASSIGN_PROVIDER = "persistent://public/default/hda-assign-provider-command-v1"
PROVIDER_ASSIGNED = "persistent://public/default/hda-provider-assigned-v1"
APPROVE_CLAIM = "persistent://public/default/hda-approve-claim-command-v1"
APPROVAL_GRANTED = "persistent://public/default/hda-approval-granted-v1"
AUTHORIZE_PAYMENT = "persistent://public/default/hda-authorize-payment-command-v1"
PAYMENT_AUTHORIZED = "persistent://public/default/hda-payment-authorized-v1"
CANCEL_ASSIGNMENT = "persistent://public/default/hda-cancel-provider-assignment-command-v1"


def record(conn, saga_id, work_id, step, action, status, details=None):
    conn.execute(
        "INSERT INTO saga_log (saga_id, work_id, step, action, status, details) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (saga_id, work_id, step, action, status, Jsonb(details or {})),
    )
    conn.commit()


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    pulsar_url = os.environ["PULSAR_URL"]
    fail_step = os.getenv("SAGA_FAIL_STEP", "").upper()
    client = pulsar.Client(pulsar_url)
    consumers = {
        topic: client.subscribe(topic, subscription_name=f"saga-{name}")
        for topic, name in {
            WORK_CREATED: "created", PROVIDER_ASSIGNED: "assigned",
            APPROVAL_GRANTED: "approved", PAYMENT_AUTHORIZED: "paid",
        }.items()
    }
    producers = {
        topic: client.create_producer(topic)
        for topic in [ASSIGN_PROVIDER, APPROVE_CLAIM, AUTHORIZE_PAYMENT, CANCEL_ASSIGNMENT]
    }
    try:
        while True:
            for topic, consumer in consumers.items():
                try:
                    message = consumer.receive(timeout_millis=50)
                except pulsar.Timeout:
                    continue
                event = json.loads(message.data())
                work_id = UUID(event["work_id"])
                with psycopg.connect(database_url) as conn:
                    saga = conn.execute(
                        "SELECT saga_id FROM saga_log WHERE work_id=%s ORDER BY occurred_at LIMIT 1",
                        (work_id,),
                    ).fetchone()
                    saga_id = saga[0] if saga else uuid4()
                    if topic == WORK_CREATED:
                        record(conn, saga_id, work_id, "CREATE", "START_SAGA", "STARTED")
                        payload = {"work_id": str(work_id), "partner_id": event["partner_id"]}
                        producers[ASSIGN_PROVIDER].send(json.dumps(payload).encode())
                        producers[ASSIGN_PROVIDER].flush()
                        record(conn, saga_id, work_id, "ASSIGN_PROVIDER", "COMMAND_SENT", "PENDING")
                    elif topic == PROVIDER_ASSIGNED:
                        record(conn, saga_id, work_id, "ASSIGN_PROVIDER", "EVENT_RECEIVED", "COMPLETED")
                        if fail_step == "APPROVAL":
                            record(conn, saga_id, work_id, "APPROVAL", "FAILURE_INJECTED", "FAILED")
                            producers[CANCEL_ASSIGNMENT].send(json.dumps({
                                "saga_id": str(saga_id), "work_id": str(work_id),
                                "reason": "controlled approval failure",
                            }).encode())
                            producers[CANCEL_ASSIGNMENT].flush()
                            record(conn, saga_id, work_id, "ASSIGN_PROVIDER", "COMPENSATE", "COMPENSATION_REQUESTED")
                        else:
                            producers[APPROVE_CLAIM].send(json.dumps(event).encode())
                            producers[APPROVE_CLAIM].flush()
                            record(conn, saga_id, work_id, "APPROVAL", "COMMAND_SENT", "PENDING")
                    elif topic == APPROVAL_GRANTED:
                        record(conn, saga_id, work_id, "APPROVAL", "EVENT_RECEIVED", "COMPLETED")
                        producers[AUTHORIZE_PAYMENT].send(json.dumps(event).encode())
                        producers[AUTHORIZE_PAYMENT].flush()
                        record(conn, saga_id, work_id, "PAYMENT", "COMMAND_SENT", "PENDING")
                    elif topic == PAYMENT_AUTHORIZED:
                        record(conn, saga_id, work_id, "PAYMENT", "EVENT_RECEIVED", "COMPLETED")
                        record(conn, saga_id, work_id, "SAGA", "TRANSACTION_COMPLETED", "COMPLETED")
                consumer.acknowledge(message)
    finally:
        for producer in producers.values():
            producer.close()
        for consumer in consumers.values():
            consumer.close()
        client.close()


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as exc:
            print(f"saga orchestrator retry: {exc}", flush=True)
            time.sleep(3)
