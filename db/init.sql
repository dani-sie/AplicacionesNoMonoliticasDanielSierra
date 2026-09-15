CREATE TABLE IF NOT EXISTS works (
  id UUID PRIMARY KEY,
  source TEXT NOT NULL,
  category TEXT NOT NULL,
  urgency TEXT NOT NULL,
  city TEXT NOT NULL,
  partner_id TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  UNIQUE (id)
);

CREATE TABLE IF NOT EXISTS outbox_events (
  id UUID PRIMARY KEY,
  aggregate_id UUID NOT NULL,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS orchestration_audit (
  id BIGSERIAL PRIMARY KEY,
  work_id UUID NOT NULL,
  event_type TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL
);

-- Each service owns its tables. The POC shares a PostgreSQL cluster only to
-- keep the local deployment small; services never query another service table.
CREATE TABLE IF NOT EXISTS provider_assignments (
  work_id UUID PRIMARY KEY,
  provider_id TEXT NOT NULL,
  status TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_approvals (
  work_id UUID PRIMARY KEY,
  provider_id TEXT NOT NULL,
  status TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
  work_id UUID PRIMARY KEY,
  status TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL
);
