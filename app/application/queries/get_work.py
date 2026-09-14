from uuid import UUID


def execute(work_id: UUID, repository):
    return repository.find(work_id)
