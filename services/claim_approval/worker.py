import json
import os
import time
from uuid import UUID

import psycopg
import pulsar


INPUT_TOPIC = "persistent://public/default/hda-approve-claim-command-v1"
OUTPUT_TOPIC = "persistent://public/default/hda-approval-granted-v1"
PAYMENT_COMMAND_TOPIC = "persistent://public/default/hda-authorize-payment-command-v1"


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    pulsar_url = os.environ["PULSAR_URL"]
    with psycopg.connect(database_url) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS claim_approvals (work_id UUID PRIMARY KEY, provider_id TEXT NOT NULL, status TEXT NOT NULL, occurred_at TIMESTAMPTZ NOT NULL)")
        conn.commit()
    while True:
        client = None
        consumer = None
        try:
            client = pulsar.Client(pulsar_url)
            consumer = client.subscribe(INPUT_TOPIC, subscription_name="claim-approval")
            producer = client.create_producer(OUTPUT_TOPIC)
            payment_command_producer = client.create_producer(PAYMENT_COMMAND_TOPIC)
            while True:
                try:
                    message = consumer.receive(timeout_millis=1000)
                except pulsar.Timeout:
                    continue
                event = json.loads(message.data())
                work_id = UUID(event["work_id"])
                with psycopg.connect(database_url) as conn:
                    inserted = conn.execute(
                        "INSERT INTO claim_approvals "
                        "(work_id, provider_id, status, occurred_at) "
                        "VALUES (%s, %s, 'APPROVED', NOW()) ON CONFLICT (work_id) DO NOTHING",
                        (work_id, event["provider_id"]),
                    ).rowcount
                    conn.commit()
                if inserted:
                    producer.send(json.dumps({"work_id": str(work_id), "provider_id": event["provider_id"], "status": "APPROVED"}).encode())
                    producer.flush()
                    payment_command_producer.send(json.dumps({"work_id": str(work_id), "status": "REQUESTED"}).encode())
                    payment_command_producer.flush()
                consumer.acknowledge(message)
        except Exception as exc:
            print(f"claim approval service retry: {exc}", flush=True)
            time.sleep(3)
        finally:
            if consumer:
                consumer.close()
            if client:
                client.close()


if __name__ == "__main__":
    main()
