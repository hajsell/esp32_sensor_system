CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS sensor_readings (
    recorded_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    device_id TEXT NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION CHECK (humidity BETWEEN 0 AND 100),
    mq2 DOUBLE PRECISION CHECK (mq2 BETWEEN 0 AND 4095),
    mq7 DOUBLE PRECISION CHECK (mq7 BETWEEN 0 AND 4095)
);

SELECT create_hypertable(
    'sensor_readings',
    by_range('recorded_at', INTERVAL '1 day'),
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS sensor_readings_device_time_idx
    ON sensor_readings (device_id, recorded_at DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_readings_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket(INTERVAL '5 minutes', recorded_at) AS bucket,
    device_id,
    avg(temperature) AS temperature_avg,
    min(temperature) AS temperature_min,
    max(temperature) AS temperature_max,
    avg(humidity) AS humidity_avg,
    min(humidity) AS humidity_min,
    max(humidity) AS humidity_max,
    avg(mq2) AS mq2_avg,
    min(mq2) AS mq2_min,
    max(mq2) AS mq2_max,
    avg(mq7) AS mq7_avg,
    min(mq7) AS mq7_min,
    max(mq7) AS mq7_max,
    count(*) AS sample_count
FROM sensor_readings
GROUP BY bucket, device_id
WITH NO DATA;

-- Łączy zapisane agregaty z najnowszymi surowymi próbkami, dzięki czemu
-- wykres nie czeka na zakończenie pierwszego pięciominutowego przedziału.
ALTER MATERIALIZED VIEW sensor_readings_5m
    SET (timescaledb.materialized_only = false);

SELECT add_continuous_aggregate_policy(
    'sensor_readings_5m',
    start_offset => INTERVAL '8 days',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

SELECT add_retention_policy(
    'sensor_readings',
    drop_after => INTERVAL '7 days',
    if_not_exists => TRUE
);
