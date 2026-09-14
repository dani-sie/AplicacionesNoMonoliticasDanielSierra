from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


class WorkStatus(StrEnum):
    ACCEPTED = "ACCEPTED"


@dataclass(frozen=True)
class WorkId:
    value: UUID


@dataclass(frozen=True)
class Location:
    city: str

    def __post_init__(self):
        if not self.city or len(self.city) > 80:
            raise ValueError("city must contain 1 to 80 characters")


@dataclass(frozen=True)
class WorkCreated:
    work_id: UUID
    source: str
    category: str
    urgency: str
    city: str
    partner_id: str
    occurred_at: datetime
    event_type: str = "WorkCreated.v1"


@dataclass
class Work:
    id: WorkId
    source: str
    category: str
    urgency: str
    location: Location
    partner_id: str
    status: WorkStatus
    created_at: datetime

    @classmethod
    def create(cls, source: str, category: str, urgency: str, city: str, partner_id: str):
        if source not in {"MARKETPLACE", "CLAIM"}:
            raise ValueError("source must be MARKETPLACE or CLAIM")
        if not category or not partner_id:
            raise ValueError("category and partner_id are required")
        if urgency not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError("urgency must be LOW, MEDIUM or HIGH")
        now = datetime.now(timezone.utc)
        work_id = uuid4()
        work = cls(WorkId(work_id), source, category, urgency, Location(city), partner_id, WorkStatus.ACCEPTED, now)
        return work, WorkCreated(work_id, source, category, urgency, city, partner_id, now)
