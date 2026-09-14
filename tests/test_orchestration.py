from uuid import uuid4
from app.orchestration.consumer import WorkCreatedConsumer


def test_orchestration_reacts_to_work_created_contract():
    work_id = uuid4()
    result = WorkCreatedConsumer().handle({"work_id": str(work_id)})

    assert result == {"work_id": work_id, "action": "START_ORCHESTRATION"}
