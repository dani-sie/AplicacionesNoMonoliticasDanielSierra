import json
import os
import time
from uuid import UUID

import psycopg
import pulsar


INPUT_TOPIC = "persistent://public/default/hda-authorize-payment-command-v1"
OUTPUT_TOPIC = "persistent://public/default/hda-payment-authorized-v1"


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    pulsar_url = os.environ["PULSAR_URL"]
    with psycopg.connect(database_url) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS payments (work_id UUID PRIMARY KEY, status TEXT NOT NULL, occurred_at TIMESTAMPTZ NOT NULL)")
        conn.commit()
    while True:
        client = None
        consumer = None
        try:
            client = pulsar.Client(pulsar_url)
            consumer = client.subscribe(INPUT_TOPIC, subscription_name="payment-compensation")
            producer = client.create_producer(OUTPUT_TOPIC)
            while True:
                try:
                    message = consumer.receive(timeout_millis=1000)
                except pulsar.Timeout:
                    continue
                event = json.loads(message.data())
                work_id = UUID(event["work_id"])
                with psycopg.connect(database_url) as conn:
                    inserted = conn.execute(
                        "INSERT INTO payments "
                        "(work_id, status, occurred_at) "
                        "VALUES (%s, 'AUTHORIZED', NOW()) ON CONFLICT (work_id) DO NOTHING",
                        (work_id,),
                    ).rowcount
                    conn.commit()
                if inserted:
                    producer.send(json.dumps({"work_id": str(work_id), "status": "AUTHORIZED"}).encode())
                    producer.flush()
                consumer.acknowledge(message)
        except Exception as exc:
            print(f"payment service retry: {exc}", flush=True)
            time.sleep(3)
        finally:
            if consumer:
                consumer.close()
            if client:
                client.close()


if __name__ == "__main__":
    main()
