from __future__ import annotations

from datetime import datetime

import requests
from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from psycopg2.extras import execute_values

SQL_DIR = "/usr/local/airflow/include/sql/openmeteo"
OPENMETEO_RAW_READY = Dataset("airflow_agents://openmeteo/raw_ready")


def fetch_and_load() -> None:
    conn_id = Variable.get("openmeteo_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("openmeteo_schema", default_var="raw_openmeteo")
    hourly_table = Variable.get("openmeteo_hourly_table", default_var="openmeteo_hourly")
    daily_table = Variable.get("openmeteo_daily_table", default_var="openmeteo_daily")

    latitude = Variable.get("openmeteo_latitude", default_var="52.52")
    longitude = Variable.get("openmeteo_longitude", default_var="13.41")
    past_days = Variable.get("openmeteo_past_days", default_var="10")
    hourly = Variable.get(
        "openmeteo_hourly",
        default_var=(
            "temperature_2m,apparent_temperature,relative_humidity_2m,"
            "precipitation,wind_speed_10m,weather_code"
        ),
    )
    daily = Variable.get(
        "openmeteo_daily",
        default_var="temperature_2m_max,temperature_2m_min,precipitation_sum",
    )

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&past_days={past_days}&hourly={hourly}&daily={daily}&timezone=auto"
    )

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    hourly_payload = payload.get("hourly", {})
    times = hourly_payload.get("time", [])
    expected_len = len(times)

    def series(values: list[object] | None, expected: int) -> list[object]:
        if values is None:
            return [None] * expected
        if len(values) != expected:
            raise ValueError("Hourly arrays have different lengths")
        return values

    temps = series(hourly_payload.get("temperature_2m"), expected_len)
    apparent_temps = series(hourly_payload.get("apparent_temperature"), expected_len)
    hums = series(hourly_payload.get("relative_humidity_2m"), expected_len)
    precips = series(hourly_payload.get("precipitation"), expected_len)
    winds = series(hourly_payload.get("wind_speed_10m"), expected_len)
    weather_codes = series(hourly_payload.get("weather_code"), expected_len)

    lat = payload.get("latitude", float(latitude))
    lon = payload.get("longitude", float(longitude))
    elevation = payload.get("elevation")
    timezone = payload.get("timezone")
    timezone_abbreviation = payload.get("timezone_abbreviation")

    hourly_rows = list(
        zip(
            times,
            temps,
            apparent_temps,
            hums,
            precips,
            winds,
            weather_codes,
            [lat] * expected_len,
            [lon] * expected_len,
            [elevation] * expected_len,
            [timezone] * expected_len,
            [timezone_abbreviation] * expected_len,
        )
    )

    daily_payload = payload.get("daily", {})
    daily_dates = daily_payload.get("time", [])
    daily_expected_len = len(daily_dates)
    max_temps = series(daily_payload.get("temperature_2m_max"), daily_expected_len)
    min_temps = series(daily_payload.get("temperature_2m_min"), daily_expected_len)
    precipitation_sum = series(daily_payload.get("precipitation_sum"), daily_expected_len)

    daily_rows = list(
        zip(
            daily_dates,
            max_temps,
            min_temps,
            precipitation_sum,
            [lat] * daily_expected_len,
            [lon] * daily_expected_len,
            [elevation] * daily_expected_len,
            [timezone] * daily_expected_len,
            [timezone_abbreviation] * daily_expected_len,
        )
    )

    if not hourly_rows and not daily_rows:
        return

    hook = PostgresHook(postgres_conn_id=conn_id)
    insert_hourly_sql = (
        f"insert into {schema}.{hourly_table} "
        "("
        "time, temperature_2m, apparent_temperature, relative_humidity_2m, "
        "precipitation, wind_speed_10m, weather_code, latitude, longitude, "
        "elevation, timezone, timezone_abbreviation"
        ") values %s on conflict do nothing"
    )
    insert_daily_sql = (
        f"insert into {schema}.{daily_table} "
        "("
        "date, temperature_2m_max, temperature_2m_min, precipitation_sum, "
        "latitude, longitude, elevation, timezone, timezone_abbreviation"
        ") values %s on conflict do nothing"
    )

    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            if hourly_rows:
                execute_values(cur, insert_hourly_sql, hourly_rows, page_size=1000)
            if daily_rows:
                execute_values(cur, insert_daily_sql, daily_rows, page_size=1000)
        conn.commit()


with DAG(
    dag_id="openmeteo_raw_ingest",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["open-meteo", "raw"],
    template_searchpath=[SQL_DIR],
) as dag:
    create_schema = PostgresOperator(
        task_id="create_schema",
        postgres_conn_id=Variable.get("openmeteo_postgres_conn_id", default_var="postgres_default"),
        sql="create_schema.sql",
        params={
            "schema": Variable.get("openmeteo_schema", default_var="raw_openmeteo"),
        },
    )

    create_table = PostgresOperator(
        task_id="create_table_hourly",
        postgres_conn_id=Variable.get("openmeteo_postgres_conn_id", default_var="postgres_default"),
        sql="create_table.sql",
        params={
            "schema": Variable.get("openmeteo_schema", default_var="raw_openmeteo"),
            "table": Variable.get("openmeteo_hourly_table", default_var="openmeteo_hourly"),
        },
    )

    create_table_daily = PostgresOperator(
        task_id="create_table_daily",
        postgres_conn_id=Variable.get("openmeteo_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_daily.sql",
        params={
            "schema": Variable.get("openmeteo_schema", default_var="raw_openmeteo"),
            "table": Variable.get("openmeteo_daily_table", default_var="openmeteo_daily"),
        },
    )

    ingest = PythonOperator(
        task_id="fetch_and_load",
        python_callable=fetch_and_load,
        outlets=[OPENMETEO_RAW_READY],
    )

    create_schema >> [create_table, create_table_daily] >> ingest
