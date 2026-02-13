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
    table = Variable.get("openmeteo_table", default_var="openmeteo_hourly")

    latitude = Variable.get("openmeteo_latitude", default_var="52.52")
    longitude = Variable.get("openmeteo_longitude", default_var="13.41")
    past_days = Variable.get("openmeteo_past_days", default_var="10")
    hourly = Variable.get(
        "openmeteo_hourly",
        default_var="temperature_2m,relative_humidity_2m,wind_speed_10m",
    )

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&past_days={past_days}&hourly={hourly}"
    )

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    hourly_payload = payload.get("hourly", {})
    times = hourly_payload.get("time", [])
    temps = hourly_payload.get("temperature_2m", [])
    hums = hourly_payload.get("relative_humidity_2m", [])
    winds = hourly_payload.get("wind_speed_10m", [])

    if not (len(times) == len(temps) == len(hums) == len(winds)):
        raise ValueError("Hourly arrays have different lengths")

    lat = payload.get("latitude", float(latitude))
    lon = payload.get("longitude", float(longitude))

    rows = list(zip(times, temps, hums, winds, [lat] * len(times), [lon] * len(times)))

    if not rows:
        return

    hook = PostgresHook(postgres_conn_id=conn_id)
    insert_sql = (
        f"insert into {schema}.{table} "
        "(time, temperature_2m, relative_humidity_2m, wind_speed_10m, latitude, longitude)"
        " values %s on conflict do nothing"
    )

    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, rows, page_size=1000)
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
        task_id="create_table",
        postgres_conn_id=Variable.get("openmeteo_postgres_conn_id", default_var="postgres_default"),
        sql="create_table.sql",
        params={
            "schema": Variable.get("openmeteo_schema", default_var="raw_openmeteo"),
            "table": Variable.get("openmeteo_table", default_var="openmeteo_hourly"),
        },
    )

    ingest = PythonOperator(
        task_id="fetch_and_load",
        python_callable=fetch_and_load,
        outlets=[OPENMETEO_RAW_READY],
    )

    create_schema >> create_table >> ingest
