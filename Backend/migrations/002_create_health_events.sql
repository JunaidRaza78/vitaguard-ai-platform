-- Migration 002: Create health_events table for Family Health Dashboard
-- Stores time-series health events (visits, vitals, medication changes, lab results)

CREATE TABLE IF NOT EXISTS health_events (
    event_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_date TIMESTAMPTZ NOT NULL,
    provider_name VARCHAR(255),
    location VARCHAR(255),
    event_data JSONB,
    severity VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_health_events_user_id ON health_events(user_id);
CREATE INDEX IF NOT EXISTS idx_health_events_event_type ON health_events(event_type);
CREATE INDEX IF NOT EXISTS idx_health_events_event_date ON health_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_health_events_user_date ON health_events(user_id, event_date DESC);
CREATE INDEX IF NOT EXISTS idx_health_events_user_type ON health_events(user_id, event_type);

-- GIN index for JSONB event_data queries
CREATE INDEX IF NOT EXISTS idx_health_events_data ON health_events USING GIN (event_data);

-- Constraints
ALTER TABLE health_events ADD CONSTRAINT chk_event_type
    CHECK (event_type IN ('visit', 'vital_reading', 'medication_change', 'lab_result', 'vaccination', 'condition_diagnosed'));

ALTER TABLE health_events ADD CONSTRAINT chk_severity
    CHECK (severity IS NULL OR severity IN ('normal', 'warning', 'critical'));
