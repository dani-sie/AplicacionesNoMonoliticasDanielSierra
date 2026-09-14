import json
import os
import pulsar
from app.domain.work_model import WorkCreated


class PulsarDomainEventPublisher:
    """Outbound adapter for domain events; the domain knows no Pulsar details."""

    def __init__(self, url: str | None = None):
        self.url = url or os.environ["PULSAR_URL"]

    def publish(self, event: WorkCreated) -> None:
        client = pulsar.Client(self.url)
        try:
            producer = client.create_producer(f"persistent://hda/work/{event.event_type}")
            producer.send(json.dumps({"work_id": str(event.work_id), "source": event.source, "category": event.category, "urgency": event.urgency, "city": event.city, "partner_id": event.partner_id, "occurred_at": event.occurred_at.isoformat()}).encode())
            producer.flush()
            producer.close()
        finally:
            client.close()
