from app.domain.work_model import Location, Work, WorkStatus


def test_create_work_returns_accepted_work_and_domain_event():
    work, event = Work.create("CLAIM", "PLUMBING", "HIGH", "Bogota", "partner-001")

    assert work.status == WorkStatus.ACCEPTED
    assert work.location == Location("Bogota")
    assert event.event_type == "WorkCreated.v1"
    assert event.work_id == work.id.value


def test_create_work_rejects_unknown_source():
    try:
        Work.create("UNKNOWN", "PLUMBING", "HIGH", "Bogota", "partner-001")
    except ValueError as exc:
        assert "source" in str(exc)
    else:
        raise AssertionError("unknown source should be rejected")


def test_create_work_rejects_unknown_urgency():
    try:
        Work.create("CLAIM", "PLUMBING", "URGENT", "Bogota", "partner-001")
    except ValueError as exc:
        assert "urgency" in str(exc)
    else:
        raise AssertionError("unknown urgency should be rejected")
