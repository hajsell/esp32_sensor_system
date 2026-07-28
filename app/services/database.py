from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo

from psycopg import sql
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

    def latest_reading(self, device_id: str) -> dict | None:
        query = """
            SELECT
                recorded_at,
                temperature,
                humidity,
                mq2,
                mq7
            FROM sensor_readings
            WHERE device_id = %s
            ORDER BY recorded_at DESC
            LIMIT 1
        """

        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (device_id,))
                row = cursor.fetchone()

        if row is None:
            return None

        result = dict(row)
        result["timestamp"] = result.pop("recorded_at").isoformat()
        return result

    def sensor_summary(
        self,
        device_id: str,
        metric: str,
        hours: int,
    ) -> dict:
        allowed_metrics = {"temperature", "humidity", "mq2", "mq7"}
        if metric not in allowed_metrics:
            raise ValueError("Nieobsługiwana metryka.")
        if not 1 <= hours <= 168:
            raise ValueError("Zakres czasu musi wynosić od 1 do 168 godzin.")

        query = sql.SQL(
            """
            SELECT
                min({metric}) AS minimum,
                max({metric}) AS maximum,
                avg({metric}) AS average,
                count({metric}) AS sample_count,
                min(recorded_at) AS period_start,
                max(recorded_at) AS period_end
            FROM sensor_readings
            WHERE device_id = %s
              AND recorded_at >= now() - (%s * INTERVAL '1 hour')
            """
        ).format(metric=sql.Identifier(metric))

        with self.pool.connection() as connection:
            row = connection.execute(query, (device_id, hours)).fetchone()

        result = dict(row)
        for key in ("minimum", "maximum", "average"):
            if result[key] is not None:
                result[key] = float(result[key])
        for key in ("period_start", "period_end"):
            if result[key] is not None:
                result[key] = result[key].isoformat()

        return {
            "device_id": device_id,
            "metric": metric,
            "hours": hours,
            **result,
        }


_instances = {}
_instances_lock = Lock()


def get_database(database_url: str, timezone: str = "Europe/Warsaw") -> SensorDatabase:
    key = (database_url, timezone)
    with _instances_lock:
        if key not in _instances:
            _instances[key] = SensorDatabase(database_url, timezone)
        return _instances[key]
