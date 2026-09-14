from typing import Protocol
from uuid import UUID
from .work_model import Work, WorkCreated


class WorkRepository(Protocol):
    def save_with_event(self, work: Work, event: WorkCreated) -> None: ...
    def find(self, work_id: UUID) -> Work | None: ...
