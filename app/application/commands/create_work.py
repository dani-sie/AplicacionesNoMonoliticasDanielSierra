from dataclasses import dataclass
from app.domain.work_model import Work


@dataclass(frozen=True)
class CreateWork:
    source: str
    category: str
    urgency: str
    city: str
    partner_id: str
    idempotency_key: str


def execute(command: CreateWork, repository) -> Work:
    existing = repository.find_by_idempotency_key(command.idempotency_key)
    if existing:
        return existing
    work, event = Work.create(command.source, command.category, command.urgency, command.city, command.partner_id)
    repository.save_with_event(work, event, command.idempotency_key)
    return work
