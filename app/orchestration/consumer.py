from uuid import UUID

from app.domain.work_model import WorkCreated


class WorkCreatedConsumer:
    """Starts orchestration from the event contract, not from the Work aggregate."""

    def handle(self, event: dict | WorkCreated) -> dict:
        # The broker delivers JSON dictionaries; domain tests may pass the typed event.
        work_id = event.work_id if isinstance(event, WorkCreated) else UUID(event["work_id"])
        return {"work_id": work_id, "action": "START_ORCHESTRATION"}
