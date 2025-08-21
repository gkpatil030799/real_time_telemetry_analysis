-- Schema for bronze (raw) data
CREATE SCHEMA IF NOT EXISTS bronze;

-- Drop if partially created earlier
DROP TABLE IF EXISTS bronze.raw_power CASCADE;
DROP TABLE IF EXISTS bronze.raw_power_stage CASCADE;

-- Raw table with composite PK including time column
CREATE TABLE bronze.raw_power (
  event_id     TEXT        NOT NULL,
  event_ts     TIMESTAMPTZ NOT NULL,
  machine_id   TEXT        NOT NULL,
  power_kw     DOUBLE PRECISION,
  voltage_v    DOUBLE PRECISION,
  current_a    DOUBLE PRECISION,
  temp_c       DOUBLE PRECISION,
  ingest_ts    TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw_payload  JSONB,
  CONSTRAINT raw_power_pk PRIMARY KEY (event_id, event_ts)
);

-- Turn into hypertable on event_ts (now allowed because PK includes event_ts)
SELECT create_hypertable('bronze.raw_power','event_ts', if_not_exists => TRUE);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_raw_power_machine_time ON bronze.raw_power(machine_id, event_ts DESC);
CREATE INDEX IF NOT EXISTS idx_raw_power_event_ts     ON bronze.raw_power(event_ts DESC);

-- Staging table (no PK)
CREATE TABLE bronze.raw_power_stage (
  event_id     TEXT,
  event_ts     TIMESTAMPTZ,
  machine_id   TEXT,
  power_kw     DOUBLE PRECISION,
  voltage_v    DOUBLE PRECISION,
  current_a    DOUBLE PRECISION,
  temp_c       DOUBLE PRECISION,
  ingest_ts    TIMESTAMPTZ,
  raw_payload  JSONB
);
