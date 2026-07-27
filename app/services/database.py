from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


TS_FMT = "%Y-%m-%d %H:%M:%S"


class SensorDatabase:
    def __init__(self, database_url: str, timezone: str = "Europe/Warsaw"):
        if not database_url:
            raise RuntimeError("Brak DATABASE_URL w konfiguracji.")
        self.timezone = timezone
        self.pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=5,
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row},
        )
        self.pool.open()

    def insert_reading(self, data: dict, device_id: str):
        recorded_at = datetime.strptime(data["timestamp"], TS_FMT).replace(
            tzinfo=ZoneInfo(self.timezone)
        )
        with self.pool.connection() as connection:
            connection.execute(
                """
                INSERT INTO sensor_readings (
                    recorded_at, device_id, temperature, humidity, mq2, mq7
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    recorded_at,
                    device_id,
                    data.get("temperature"),
                    data.get("humidity"),
                    data.get("mq2"),
                    data.get("mq7"),
                ),
            )

    def history_24h(self, device_id: str) -> list[dict]:
        with self.pool.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    to_char(bucket AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
                    temperature_avg AS temperature,
                    humidity_avg AS humidity,
                    mq2_avg AS mq2,
                    mq7_avg AS mq7
                FROM sensor_readings_5m
                WHERE device_id = %s
                  AND bucket >= now() - INTERVAL '24 hours'
                ORDER BY bucket
                """,
                (self.timezone, device_id),
            ).fetchall()
        return [dict(row) for row in rows]


_instances = {}
_instances_lock = Lock()


def get_database(database_url: str, timezone: str = "Europe/Warsaw") -> SensorDatabase:
    key = (database_url, timezone)
    with _instances_lock:
        if key not in _instances:
            _instances[key] = SensorDatabase(database_url, timezone)
        return _instances[key]
