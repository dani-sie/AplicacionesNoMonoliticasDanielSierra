import json
import os
import time
from uuid import UUID

import psycopg
import pulsar

from app.orchestration.consumer import WorkCreatedConsumer


TOPIC = "persistent://public/default/hda-work-created-v1"
COMMAND_TOPIC = "persistent://public/default/hda-assign-provider-command-v1"


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    pulsar_url = os.environ["PULSAR_URL"]
    while True:
        client = None
        consumer = None
        try:
            client = pulsar.Client(pulsar_url)
            consumer = client.subscribe(TOPIC, subscription_name="orchestration-audit")
            command_producer = client.create_producer(COMMAND_TOPIC)
            handler = WorkCreatedConsumer()
            while True:
                message = consumer.receive(timeout_millis=1000)
                event = json.loads(message.data())
                result = handler.handle(event)
                with psycopg.connect(database_url) as conn:
                    conn.execute(
                        "INSERT INTO orchestration_audit (work_id, event_type, occurred_at) "
                        "VALUES (%s, %s, NOW())",
                        (UUID(str(result["work_id"])), "WorkCreated.v1"),
                    )
                    conn.commit()
                command_producer.send(json.dumps(event).encode())
                command_producer.flush()
                consumer.acknowledge(message)
        except pulsar.Timeout:
            continue
        except Exception as exc:
            print(f"event consumer retry: {exc}", flush=True)
            time.sleep(3)
        finally:
            if consumer:
                consumer.close()
            if client:
                client.close()


if __name__ == "__main__":
    main()
