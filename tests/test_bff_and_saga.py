import json
import os
import pytest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql://hda:hda@localhost:5432/hda")

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.interfaces import bff


def test_bff_starts_saga_without_exposing_domain_details(monkeypatch):
    work_id = uuid4()
    monkeypatch.setattr(
        bff,
        "create",
        lambda command, repository: SimpleNamespace(id=SimpleNamespace(value=work_id)),
    )

    response = TestClient(bff.app).post(
        "/api/v1/sagas/works",
        headers={"Idempotency-Key": "test-bff-001"},
        json={
            "source": "CLAIM",
            "category": "PLUMBING",
            "urgency": "HIGH",
            "city": "Bogota",
            "partner_id": "partner-test",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "work_id": str(work_id),
        "status": "STARTED",
        "saga_status": "PENDING",
    }


def test_compensation_contracts_define_correlation_fields():
    root = Path(__file__).parents[1]
    for filename in [
        "cancel_provider_assignment_command.v1.json",
        "reject_claim_command.v1.json",
    ]:
        contract = json.loads((root / "contracts" / filename).read_text())
        assert contract["type"] == "object"
        assert set(["saga_id", "work_id", "reason"]).issubset(contract["required"])
