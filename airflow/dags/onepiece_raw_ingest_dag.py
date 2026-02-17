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

SQL_DIR = "/usr/local/airflow/include/sql/onepiece"
ONEPIECE_RAW_READY = Dataset("airflow_agents://onepiece/raw_ready")


def fetch_and_load_onepiece() -> None:
    """Fetch One Piece data from api.api-onepiece.com and load into normalized tables."""
    conn_id = Variable.get("onepiece_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("onepiece_schema", default_var="raw_onepiece")
    base_url = "https://api.api-onepiece.com/v2"
    language = Variable.get("onepiece_language", default_var="en")

    hook = PostgresHook(postgres_conn_id=conn_id)

    # ------------------------------------------------------------------
    # Characters
    # ------------------------------------------------------------------
    print(f"Fetching characters from {base_url}/characters/{language} ...")
    resp = requests.get(f"{base_url}/characters/{language}", timeout=30)
    resp.raise_for_status()
    characters = resp.json()
    print(f"Fetched {len(characters)} characters.")

    character_rows = []
    for c in characters:
        crew = c.get("crew") or {}
        fruit = c.get("fruit") or {}
        character_rows.append((
            c.get("id"),
            c.get("name"),
            c.get("size"),
            c.get("age"),
            c.get("bounty"),
            c.get("job"),
            c.get("status"),
            crew.get("id"),
            crew.get("name"),
            crew.get("roman_name"),
            crew.get("status"),
            crew.get("is_yonko"),
            fruit.get("id") if fruit else None,
            fruit.get("name") if fruit else None,
            fruit.get("roman_name") if fruit else None,
            fruit.get("type") if fruit else None,
        ))

    # ------------------------------------------------------------------
    # Devil Fruits
    # ------------------------------------------------------------------
    print(f"Fetching fruits from {base_url}/fruits/{language} ...")
    resp = requests.get(f"{base_url}/fruits/{language}", timeout=30)
    resp.raise_for_status()
    fruits = resp.json()
    print(f"Fetched {len(fruits)} fruits.")

    fruit_rows = []
    for f in fruits:
        fruit_rows.append((
            f.get("id"),
            f.get("name"),
            f.get("roman_name"),
            f.get("type"),
            f.get("description"),
            f.get("filename"),
        ))

    # ------------------------------------------------------------------
    # Sagas
    # ------------------------------------------------------------------
    print(f"Fetching sagas from {base_url}/sagas/{language} ...")
    resp = requests.get(f"{base_url}/sagas/{language}", timeout=30)
    resp.raise_for_status()
    sagas = resp.json()
    print(f"Fetched {len(sagas)} sagas.")

    saga_rows = []
    for s in sagas:
        saga_rows.append((
            s.get("id"),
            s.get("title"),
            s.get("saga_number"),
            s.get("saga_chapitre"),
            s.get("saga_volume"),
            s.get("saga_episode"),
        ))

    # ------------------------------------------------------------------
    # Insert into Postgres
    # ------------------------------------------------------------------
    with hook.get_conn() as conn:
        with conn.cursor() as cur:

            if character_rows:
                sql = (
                    f"insert into {schema}.onepiece_characters "
                    "(id, name, size, age, bounty, job, status, "
                    "crew_id, crew_name, crew_roman_name, crew_status, crew_is_yonko, "
                    "fruit_id, fruit_name, fruit_roman_name, fruit_type) "
                    "values %s on conflict (id) do nothing"
                )
                execute_values(cur, sql, character_rows, page_size=500)
                print(f"Inserted {len(character_rows)} character records")

            if fruit_rows:
                sql = (
                    f"insert into {schema}.onepiece_fruits "
                    "(id, name, roman_name, type, description, image_url) "
                    "values %s on conflict (id) do nothing"
                )
                execute_values(cur, sql, fruit_rows, page_size=500)
                print(f"Inserted {len(fruit_rows)} fruit records")

            if saga_rows:
                sql = (
                    f"insert into {schema}.onepiece_sagas "
                    "(id, title, saga_number, saga_chapitre, saga_volume, saga_episode) "
                    "values %s on conflict (id) do nothing"
                )
                execute_values(cur, sql, saga_rows, page_size=100)
                print(f"Inserted {len(saga_rows)} saga records")

        conn.commit()

    print("One Piece data loading completed successfully!")


with DAG(
    dag_id="onepiece_raw_ingest",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["one-piece", "raw"],
    template_searchpath=[SQL_DIR],
) as dag:

    create_schema = PostgresOperator(
        task_id="create_schema",
        postgres_conn_id=Variable.get("onepiece_postgres_conn_id", default_var="postgres_default"),
        sql="create_schema.sql",
        params={
            "schema": Variable.get("onepiece_schema", default_var="raw_onepiece"),
        },
    )

    create_table_characters = PostgresOperator(
        task_id="create_table_onepiece_characters",
        postgres_conn_id=Variable.get("onepiece_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_onepiece_characters.sql",
        params={
            "schema": Variable.get("onepiece_schema", default_var="raw_onepiece"),
        },
    )

    create_table_fruits = PostgresOperator(
        task_id="create_table_onepiece_fruits",
        postgres_conn_id=Variable.get("onepiece_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_onepiece_fruits.sql",
        params={
            "schema": Variable.get("onepiece_schema", default_var="raw_onepiece"),
        },
    )

    create_table_sagas = PostgresOperator(
        task_id="create_table_onepiece_sagas",
        postgres_conn_id=Variable.get("onepiece_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_onepiece_sagas.sql",
        params={
            "schema": Variable.get("onepiece_schema", default_var="raw_onepiece"),
        },
    )

    ingest = PythonOperator(
        task_id="fetch_and_load_onepiece",
        python_callable=fetch_and_load_onepiece,
        outlets=[ONEPIECE_RAW_READY],
    )

    create_schema >> [create_table_characters, create_table_fruits, create_table_sagas]
    [create_table_characters, create_table_fruits, create_table_sagas] >> ingest
