import os
from uuid import UUID

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from app.application.commands.create_work import CreateWork, execute as create
from app.infrastructure.persistence.work_postgres import PostgresWorkRepository


app = FastAPI(title="HdA CSaaS BFF", version="0.1.0")
repository = PostgresWorkRepository()


class SagaWorkRequest(BaseModel):
    source: str
    category: str = Field(min_length=1, max_length=80)
    urgency: str
    city: str = Field(min_length=1, max_length=80)
    partner_id: str = Field(min_length=1, max_length=80)


@app.post("/api/v1/sagas/works", status_code=202)
def start_saga(body: SagaWorkRequest, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=120)):
    try:
        work = create(CreateWork(**body.model_dump(), idempotency_key=idempotency_key), repository)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"work_id": str(work.id.value), "status": "STARTED", "saga_status": "PENDING"}


@app.get("/api/v1/sagas/{work_id}")
def saga_status(work_id: UUID):
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        rows = conn.execute(
            "SELECT step, action, status, occurred_at FROM saga_log "
            "WHERE work_id=%s ORDER BY id",
            (work_id,),
        ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="saga not found")
    return {
        "work_id": str(work_id),
        "status": rows[-1]["status"],
        "steps": [dict(row) for row in rows],
    }
