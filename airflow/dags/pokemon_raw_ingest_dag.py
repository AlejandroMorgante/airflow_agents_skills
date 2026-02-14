from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from psycopg2.extras import execute_values

SQL_DIR = "/usr/local/airflow/include/sql/pokemon"
POKEMON_RAW_READY = Dataset("airflow_agents://pokemon/raw_ready")


def fetch_pokemon_details(pokemon_url: str, max_retries: int = 3) -> dict | None:
    """Fetch details for a single Pokemon with retry logic."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(pokemon_url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to fetch {pokemon_url} after {max_retries} attempts: {e}")
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
    return None


def fetch_and_load_pokemon() -> None:
    """Fetch Pokemon data from PokeAPI and load into normalized tables."""
    conn_id = Variable.get("pokemon_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("pokemon_schema", default_var="raw_pokemon")
    limit = int(Variable.get("pokemon_limit", default_var="500"))
    max_workers = int(Variable.get("pokemon_max_workers", default_var="10"))

    # Fetch list of Pokemon
    list_url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}"
    resp = requests.get(list_url, timeout=30)
    resp.raise_for_status()
    pokemon_list = resp.json().get("results", [])

    print(f"Fetching details for {len(pokemon_list)} Pokemon using {max_workers} workers...")

    # Fetch details concurrently
    pokemon_details = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(fetch_pokemon_details, p["url"]): p["name"]
            for p in pokemon_list
        }

        for future in as_completed(future_to_url):
            pokemon_name = future_to_url[future]
            try:
                data = future.result()
                if data:
                    pokemon_details.append(data)
                    if len(pokemon_details) % 50 == 0:
                        print(f"Fetched {len(pokemon_details)} Pokemon so far...")
                else:
                    print(f"Skipping {pokemon_name} due to fetch failure")
            except Exception as e:
                print(f"Error processing {pokemon_name}: {e}")

            # Rate limiting
            time.sleep(0.1)

    if not pokemon_details:
        print("No Pokemon data to load")
        return

    print(f"Successfully fetched {len(pokemon_details)} Pokemon. Preparing data for insertion...")

    # Prepare data for insertion
    pokemon_rows = []
    types_rows = []
    stats_rows = []
    abilities_rows = []

    for poke in pokemon_details:
        pokemon_id = poke.get("id")

        # Main Pokemon table
        pokemon_rows.append((
            pokemon_id,
            poke.get("name"),
            poke.get("height"),
            poke.get("weight"),
            poke.get("base_experience"),
            poke.get("sprites", {}).get("front_default")
        ))

        # Types
        for type_data in poke.get("types", []):
            types_rows.append((
                pokemon_id,
                type_data.get("slot"),
                type_data.get("type", {}).get("name")
            ))

        # Stats
        for stat_data in poke.get("stats", []):
            stats_rows.append((
                pokemon_id,
                stat_data.get("stat", {}).get("name"),
                stat_data.get("base_stat"),
                stat_data.get("effort")
            ))

        # Abilities
        for ability_data in poke.get("abilities", []):
            abilities_rows.append((
                pokemon_id,
                ability_data.get("slot"),
                ability_data.get("ability", {}).get("name"),
                ability_data.get("is_hidden", False)
            ))

    # Insert data into database
    hook = PostgresHook(postgres_conn_id=conn_id)

    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            # Insert Pokemon
            if pokemon_rows:
                pokemon_sql = (
                    f"insert into {schema}.pokemon "
                    "(id, name, height, weight, base_experience, sprite_front_default) "
                    "values %s on conflict (id) do nothing"
                )
                execute_values(cur, pokemon_sql, pokemon_rows, page_size=1000)
                print(f"Inserted {len(pokemon_rows)} Pokemon records")

            # Insert Types
            if types_rows:
                types_sql = (
                    f"insert into {schema}.pokemon_types "
                    "(pokemon_id, slot, type_name) "
                    "values %s on conflict (pokemon_id, slot) do nothing"
                )
                execute_values(cur, types_sql, types_rows, page_size=1000)
                print(f"Inserted {len(types_rows)} Pokemon type records")

            # Insert Stats
            if stats_rows:
                stats_sql = (
                    f"insert into {schema}.pokemon_stats "
                    "(pokemon_id, stat_name, base_stat, effort) "
                    "values %s on conflict (pokemon_id, stat_name) do nothing"
                )
                execute_values(cur, stats_sql, stats_rows, page_size=1000)
                print(f"Inserted {len(stats_rows)} Pokemon stat records")

            # Insert Abilities
            if abilities_rows:
                abilities_sql = (
                    f"insert into {schema}.pokemon_abilities "
                    "(pokemon_id, slot, ability_name, is_hidden) "
                    "values %s on conflict (pokemon_id, slot) do nothing"
                )
                execute_values(cur, abilities_sql, abilities_rows, page_size=1000)
                print(f"Inserted {len(abilities_rows)} Pokemon ability records")

        conn.commit()

    print("Pokemon data loading completed successfully!")


with DAG(
    dag_id="pokemon_raw_ingest",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["pokemon", "raw"],
    template_searchpath=[SQL_DIR],
) as dag:
    create_schema = PostgresOperator(
        task_id="create_schema",
        postgres_conn_id=Variable.get("pokemon_postgres_conn_id", default_var="postgres_default"),
        sql="create_schema.sql",
        params={
            "schema": Variable.get("pokemon_schema", default_var="raw_pokemon"),
        },
    )

    create_table_pokemon = PostgresOperator(
        task_id="create_table_pokemon",
        postgres_conn_id=Variable.get("pokemon_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_pokemon.sql",
        params={
            "schema": Variable.get("pokemon_schema", default_var="raw_pokemon"),
        },
    )

    create_table_types = PostgresOperator(
        task_id="create_table_pokemon_types",
        postgres_conn_id=Variable.get("pokemon_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_pokemon_types.sql",
        params={
            "schema": Variable.get("pokemon_schema", default_var="raw_pokemon"),
        },
    )

    create_table_stats = PostgresOperator(
        task_id="create_table_pokemon_stats",
        postgres_conn_id=Variable.get("pokemon_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_pokemon_stats.sql",
        params={
            "schema": Variable.get("pokemon_schema", default_var="raw_pokemon"),
        },
    )

    create_table_abilities = PostgresOperator(
        task_id="create_table_pokemon_abilities",
        postgres_conn_id=Variable.get("pokemon_postgres_conn_id", default_var="postgres_default"),
        sql="create_table_pokemon_abilities.sql",
        params={
            "schema": Variable.get("pokemon_schema", default_var="raw_pokemon"),
        },
    )

    ingest = PythonOperator(
        task_id="fetch_and_load_pokemon",
        python_callable=fetch_and_load_pokemon,
        outlets=[POKEMON_RAW_READY],
    )

    create_schema >> create_table_pokemon
    create_schema >> [create_table_types, create_table_stats, create_table_abilities]
    [create_table_pokemon, create_table_types, create_table_stats, create_table_abilities] >> ingest
