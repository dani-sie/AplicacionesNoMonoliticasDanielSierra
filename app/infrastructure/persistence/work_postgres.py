import json
import os
from uuid import UUID
import psycopg
from psycopg.rows import dict_row
from app.domain.work_model import Location, Work, WorkCreated, WorkId, WorkStatus


class PostgresWorkRepository:
    def __init__(self, url: str | None = None):
        self.url = url or os.environ["DATABASE_URL"]

    def save_with_event(self, work: Work, event: WorkCreated, idempotency_key: str):
        payload = {"work_id": str(event.work_id), "source": event.source, "category": event.category, "urgency": event.urgency, "city": event.city, "partner_id": event.partner_id, "occurred_at": event.occurred_at.isoformat()}
        with psycopg.connect(self.url) as conn:
            conn.execute("INSERT INTO works (id, source, category, urgency, city, partner_id, status, created_at, idempotency_key) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (work.id.value, work.source, work.category, work.urgency, work.location.city, work.partner_id, work.status.value, work.created_at, idempotency_key))
            conn.execute("INSERT INTO outbox_events VALUES (%s,%s,%s,%s,%s,NULL)", (event.work_id, event.work_id, event.event_type, json.dumps(payload), event.occurred_at))
            conn.commit()

    def find_by_idempotency_key(self, idempotency_key: str):
        with psycopg.connect(self.url, row_factory=dict_row) as conn:
            row = conn.execute("SELECT * FROM works WHERE idempotency_key=%s", (idempotency_key,)).fetchone()
            return self._to_work(row) if row else None

    def find(self, work_id: UUID):
        with psycopg.connect(self.url, row_factory=dict_row) as conn:
            row = conn.execute("SELECT * FROM works WHERE id=%s", (work_id,)).fetchone()
            if not row:
                return None
            return self._to_work(row)

    @staticmethod
    def _to_work(row):
        return Work(WorkId(row["id"]), row["source"], row["category"], row["urgency"], Location(row["city"]), row["partner_id"], WorkStatus(row["status"]), row["created_at"])
