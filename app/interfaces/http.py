from uuid import UUID
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from app.application.commands.create_work import CreateWork, execute as create
from app.application.queries.get_work import execute as get
from app.infrastructure.persistence.work_postgres import PostgresWorkRepository

app = FastAPI(title="HdA Work Management", version="0.1.0")
repository = PostgresWorkRepository()


class WorkRequest(BaseModel):
    source: str
    category: str = Field(min_length=1, max_length=80)
    urgency: str
    city: str = Field(min_length=1, max_length=80)
    partner_id: str = Field(min_length=1, max_length=80)


@app.post("/works", status_code=201)
def create_work(body: WorkRequest, idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=120)):
    try:
        result = create(CreateWork(**body.model_dump(), idempotency_key=idempotency_key), repository)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": str(result.id.value), "status": result.status, "source": result.source}


@app.get("/works/{work_id}")
def read_work(work_id: UUID):
    result = get(work_id, repository)
    if not result:
        raise HTTPException(status_code=404, detail="work not found")
    return {"id": str(result.id.value), "status": result.status, "source": result.source, "category": result.category, "urgency": result.urgency, "city": result.location.city, "partner_id": result.partner_id}
