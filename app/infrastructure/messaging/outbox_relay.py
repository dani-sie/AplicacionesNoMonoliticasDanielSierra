import json
import os
import time

import psycopg
import pulsar
from psycopg.rows import dict_row


TOPIC = "persistent://public/default/hda-work-created-v1"


def publish_pending_once() -> bool:
    database_url = os.environ["DATABASE_URL"]
    pulsar_url = os.environ["PULSAR_URL"]
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        row = conn.execute(
            "SELECT id, payload FROM outbox_events "
            "WHERE published_at IS NULL ORDER BY occurred_at FOR UPDATE SKIP LOCKED LIMIT 1"
        ).fetchone()
        if not row:
            return False

        client = pulsar.Client(pulsar_url)
        try:
            producer = client.create_producer(TOPIC)
            producer.send(json.dumps(row["payload"]).encode())
            producer.flush()
            producer.close()
        finally:
            client.close()

        conn.execute("UPDATE outbox_events SET published_at=NOW() WHERE id=%s", (row["id"],))
        conn.commit()
        return True


def main() -> None:
    while True:
        try:
            publish_pending_once()
        except Exception as exc:
            print(f"outbox relay retry: {exc}", flush=True)
            time.sleep(3)
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
