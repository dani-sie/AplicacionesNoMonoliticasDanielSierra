import json
import os
import time
from uuid import UUID

import psycopg
import pulsar


INPUT_TOPIC = "persistent://public/default/hda-cancel-provider-assignment-command-v1"
OUTPUT_TOPIC = "persistent://public/default/hda-provider-assignment-cancelled-v1"


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    pulsar_url = os.environ["PULSAR_URL"]
    client = pulsar.Client(pulsar_url)
    consumer = client.subscribe(INPUT_TOPIC, subscription_name="provider-assignment-compensation")
    producer = client.create_producer(OUTPUT_TOPIC)
    try:
        while True:
            try:
                message = consumer.receive(timeout_millis=1000)
            except pulsar.Timeout:
                continue
            command = json.loads(message.data())
            work_id = UUID(command["work_id"])
            with psycopg.connect(database_url) as conn:
                conn.execute(
                    "UPDATE provider_assignments SET status='CANCELLED', occurred_at=NOW() WHERE work_id=%s",
                    (work_id,),
                )
                conn.execute(
                    "INSERT INTO saga_log (saga_id, work_id, step, action, status, details) "
                    "VALUES (%s, %s, 'ASSIGN_PROVIDER', 'COMPENSATION_COMPLETED', 'COMPENSATED', %s)",
                    (UUID(command["saga_id"]), work_id, json.dumps({"reason": command["reason"]})),
                )
                conn.execute(
                    "INSERT INTO saga_log (saga_id, work_id, step, action, status, details) "
                    "VALUES (%s, %s, 'SAGA', 'TRANSACTION_COMPENSATED', 'COMPENSATED', %s)",
                    (UUID(command["saga_id"]), work_id, json.dumps({"compensated_step": "ASSIGN_PROVIDER"})),
                )
                conn.commit()
            producer.send(json.dumps(command | {"status": "COMPENSATED"}).encode())
            producer.flush()
            consumer.acknowledge(message)
    finally:
        producer.close()
        consumer.close()
        client.close()


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as exc:
            print(f"compensation service retry: {exc}", flush=True)
            time.sleep(3)
