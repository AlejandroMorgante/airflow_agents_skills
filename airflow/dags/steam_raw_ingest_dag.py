from __future__ import annotations

from datetime import datetime, timezone

import requests
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from psycopg2.extras import Json, execute_values

SQL_DIR = "/usr/local/airflow/include/sql/steam"
DEFAULT_TARGET_APP_IDS = [10, 562810, 2383760]
DEFAULT_APP_NAME_BY_ID = {
    10: "Counter-Strike",
    562810: "MONOPOLY PLUS",
    2383760: "Monopoly Madness",
}


def _parse_target_app_ids(raw_value: str) -> list[int]:
    app_ids = []
    for token in raw_value.split(","):
        token = token.strip()
        if not token:
            continue
        app_ids.append(int(token))
    return app_ids


def _insert_fetch_log(
    cur,
    schema: str,
    table: str,
    source: str,
    endpoint: str,
    appid: int | None,
    status_code: int | None,
    ok: bool,
    error_message: str | None,
    payload: dict | list | None,
) -> None:
    cur.execute(
        f"""
        insert into {schema}.{table}
          (source, endpoint, appid, status_code, ok, error_message, payload)
        values
          (%s, %s, %s, %s, %s, %s, %s)
        """,
        (source, endpoint, appid, status_code, ok, error_message, Json(payload) if payload is not None else None),
    )


def load_target_apps() -> list[int]:
    conn_id = Variable.get("steam_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("steam_schema", default_var="raw_steam")
    app_list_table = Variable.get("steam_app_list_table", default_var="steam_app_list")

    target_ids_raw = Variable.get(
        "steam_target_app_ids",
        default_var=",".join(str(app_id) for app_id in DEFAULT_TARGET_APP_IDS),
    )
    target_ids = _parse_target_app_ids(target_ids_raw)

    rows = [(app_id, DEFAULT_APP_NAME_BY_ID.get(app_id)) for app_id in target_ids]

    if not rows:
        return []

    insert_sql = (
        f"insert into {schema}.{app_list_table} (appid, name) values %s "
        "on conflict (appid) do update set name = excluded.name, ingested_at = now()"
    )

    hook = PostgresHook(postgres_conn_id=conn_id)
    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, rows, page_size=1000)
        conn.commit()

    return target_ids


def fetch_app_details_and_load(ti) -> None:
    conn_id = Variable.get("steam_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("steam_schema", default_var="raw_steam")
    app_details_table = Variable.get("steam_app_details_table", default_var="steam_app_details")
    source_fetch_log_table = Variable.get("steam_source_fetch_log_table", default_var="steam_source_fetch_log")
    app_ids = ti.xcom_pull(task_ids="load_target_apps") or []

    if not app_ids:
        return

    app_details_url = Variable.get(
        "steam_appdetails_url",
        default_var="https://store.steampowered.com/api/appdetails",
    )
    headers = {"User-Agent": "airflow-agents-skills/1.0"}

    rows = []
    hook = PostgresHook(postgres_conn_id=conn_id)
    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            for appid in app_ids:
                status_code = None
                success = False
                data = None
                error_message = None
                try:
                    response = requests.get(
                        app_details_url,
                        params={"appids": appid},
                        headers=headers,
                        timeout=30,
                    )
                    status_code = response.status_code
                    response.raise_for_status()
                    payload = response.json()
                    app_payload = payload.get(str(appid), {})
                    success = bool(app_payload.get("success", False))
                    data = app_payload.get("data") if success else None
                except requests.RequestException as exc:
                    error_message = str(exc)
                    data = None

                _insert_fetch_log(
                    cur=cur,
                    schema=schema,
                    table=source_fetch_log_table,
                    source="steam_store_appdetails",
                    endpoint=app_details_url,
                    appid=appid,
                    status_code=status_code,
                    ok=success,
                    error_message=error_message,
                    payload={"name": (data or {}).get("name")},
                )

                rows.append(
                    (
                        int(appid),
                        success,
                        status_code,
                        (data or {}).get("type"),
                        (data or {}).get("name"),
                        (data or {}).get("is_free"),
                        (data or {}).get("required_age"),
                        Json((data or {}).get("price_overview")),
                        Json((data or {}).get("developers")),
                        Json((data or {}).get("publishers")),
                        Json((data or {}).get("categories")),
                        Json((data or {}).get("genres")),
                        Json((data or {}).get("release_date")),
                        Json(data),
                    )
                )

            if rows:
                insert_sql = (
                    f"insert into {schema}.{app_details_table} ("
                    "appid, success, status_code, type, name, is_free, required_age, price_overview, developers, "
                    "publishers, categories, genres, release_date, payload"
                    ") values %s "
                    "on conflict (appid) do update set "
                    "success = excluded.success, "
                    "status_code = excluded.status_code, "
                    "type = excluded.type, "
                    "name = excluded.name, "
                    "is_free = excluded.is_free, "
                    "required_age = excluded.required_age, "
                    "price_overview = excluded.price_overview, "
                    "developers = excluded.developers, "
                    "publishers = excluded.publishers, "
                    "categories = excluded.categories, "
                    "genres = excluded.genres, "
                    "release_date = excluded.release_date, "
                    "payload = excluded.payload, "
                    "ingested_at = now()"
                )
                execute_values(cur, insert_sql, rows, page_size=200)

        conn.commit()


def fetch_steamcharts_timeseries_and_load(ti) -> None:
    conn_id = Variable.get("steam_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("steam_schema", default_var="raw_steam")
    steamcharts_timeseries_table = Variable.get(
        "steamcharts_timeseries_table", default_var="steamcharts_timeseries"
    )
    source_fetch_log_table = Variable.get("steam_source_fetch_log_table", default_var="steam_source_fetch_log")
    app_ids = ti.xcom_pull(task_ids="load_target_apps") or []

    if not app_ids:
        return

    hook = PostgresHook(postgres_conn_id=conn_id)
    headers = {"User-Agent": "airflow-agents-skills/1.0"}

    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            for appid in app_ids:
                endpoint = f"https://steamcharts.com/app/{appid}/chart-data.json"
                status_code = None
                error_message = None
                rows = []

                try:
                    response = requests.get(endpoint, headers=headers, timeout=30)
                    status_code = response.status_code
                    response.raise_for_status()
                    payload = response.json()

                    if not isinstance(payload, list):
                        raise ValueError("SteamCharts chart-data payload is not a list")

                    for point in payload:
                        if not isinstance(point, list) or len(point) != 2:
                            continue
                        ts_ms, concurrent_players = point
                        observed_at = datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=timezone.utc)
                        rows.append(("steamcharts", int(appid), observed_at, int(concurrent_players)))

                    _insert_fetch_log(
                        cur=cur,
                        schema=schema,
                        table=source_fetch_log_table,
                        source="steamcharts_chart_data",
                        endpoint=endpoint,
                        appid=appid,
                        status_code=status_code,
                        ok=True,
                        error_message=None,
                        payload={"points": len(rows)},
                    )
                except Exception as exc:  # noqa: BLE001
                    error_message = str(exc)
                    _insert_fetch_log(
                        cur=cur,
                        schema=schema,
                        table=source_fetch_log_table,
                        source="steamcharts_chart_data",
                        endpoint=endpoint,
                        appid=appid,
                        status_code=status_code,
                        ok=False,
                        error_message=error_message,
                        payload=None,
                    )

                if rows:
                    insert_sql = (
                        f"insert into {schema}.{steamcharts_timeseries_table} ("
                        "source, appid, observed_at, concurrent_players"
                        ") values %s "
                        "on conflict (source, appid, observed_at) do update set "
                        "concurrent_players = excluded.concurrent_players, "
                        "ingested_at = now()"
                    )
                    execute_values(cur, insert_sql, rows, page_size=1000)

        conn.commit()


def probe_steamdb_access(ti) -> None:
    conn_id = Variable.get("steam_postgres_conn_id", default_var="postgres_default")
    schema = Variable.get("steam_schema", default_var="raw_steam")
    source_fetch_log_table = Variable.get("steam_source_fetch_log_table", default_var="steam_source_fetch_log")
    app_ids = ti.xcom_pull(task_ids="load_target_apps") or []

    if not app_ids:
        return

    hook = PostgresHook(postgres_conn_id=conn_id)
    headers = {"User-Agent": "airflow-agents-skills/1.0"}

    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            for appid in app_ids:
                endpoint = f"https://steamdb.info/app/{appid}/charts/"
                status_code = None
                ok = False
                error_message = None
                body_excerpt = None
                try:
                    response = requests.get(endpoint, headers=headers, timeout=30)
                    status_code = response.status_code
                    body_excerpt = response.text[:3000].lower()
                    blocked = (
                        "just a moment" in body_excerpt
                        or "enable javascript and cookies" in body_excerpt
                        or "cf_chl" in body_excerpt
                    )
                    ok = response.ok and not blocked
                    if blocked:
                        error_message = "Blocked by Cloudflare challenge"
                except requests.RequestException as exc:
                    error_message = str(exc)

                _insert_fetch_log(
                    cur=cur,
                    schema=schema,
                    table=source_fetch_log_table,
                    source="steamdb_charts_probe",
                    endpoint=endpoint,
                    appid=appid,
                    status_code=status_code,
                    ok=ok,
                    error_message=error_message,
                    payload={"excerpt": body_excerpt[:400] if body_excerpt else None},
                )

        conn.commit()


with DAG(
    dag_id="steam_raw_ingest",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["steam", "raw"],
    template_searchpath=[SQL_DIR],
) as dag:
    create_schema = PostgresOperator(
        task_id="create_schema",
        postgres_conn_id=Variable.get("steam_postgres_conn_id", default_var="postgres_default"),
        sql="create_schema.sql",
        params={
            "schema": Variable.get("steam_schema", default_var="raw_steam"),
        },
    )

    create_app_list_table = PostgresOperator(
        task_id="create_app_list_table",
        postgres_conn_id=Variable.get("steam_postgres_conn_id", default_var="postgres_default"),
        sql="create_app_list_table.sql",
        params={
            "schema": Variable.get("steam_schema", default_var="raw_steam"),
            "app_list_table": Variable.get("steam_app_list_table", default_var="steam_app_list"),
        },
    )

    create_app_details_table = PostgresOperator(
        task_id="create_app_details_table",
        postgres_conn_id=Variable.get("steam_postgres_conn_id", default_var="postgres_default"),
        sql="create_app_details_table.sql",
        params={
            "schema": Variable.get("steam_schema", default_var="raw_steam"),
            "app_details_table": Variable.get(
                "steam_app_details_table",
                default_var="steam_app_details",
            ),
        },
    )

    create_steamcharts_timeseries_table = PostgresOperator(
        task_id="create_steamcharts_timeseries_table",
        postgres_conn_id=Variable.get("steam_postgres_conn_id", default_var="postgres_default"),
        sql="create_steamcharts_timeseries_table.sql",
        params={
            "schema": Variable.get("steam_schema", default_var="raw_steam"),
            "steamcharts_timeseries_table": Variable.get(
                "steamcharts_timeseries_table", default_var="steamcharts_timeseries"
            ),
        },
    )

    create_source_fetch_log_table = PostgresOperator(
        task_id="create_source_fetch_log_table",
        postgres_conn_id=Variable.get("steam_postgres_conn_id", default_var="postgres_default"),
        sql="create_source_fetch_log_table.sql",
        params={
            "schema": Variable.get("steam_schema", default_var="raw_steam"),
            "source_fetch_log_table": Variable.get(
                "steam_source_fetch_log_table", default_var="steam_source_fetch_log"
            ),
        },
    )

    load_apps = PythonOperator(
        task_id="load_target_apps",
        python_callable=load_target_apps,
    )

    fetch_app_details = PythonOperator(
        task_id="fetch_app_details",
        python_callable=fetch_app_details_and_load,
    )

    fetch_steamcharts_timeseries = PythonOperator(
        task_id="fetch_steamcharts_timeseries",
        python_callable=fetch_steamcharts_timeseries_and_load,
    )

    probe_steamdb = PythonOperator(
        task_id="probe_steamdb",
        python_callable=probe_steamdb_access,
    )

    (
        create_schema
        >> create_app_list_table
        >> create_app_details_table
        >> create_steamcharts_timeseries_table
        >> create_source_fetch_log_table
        >> load_apps
    )
    load_apps >> [fetch_app_details, fetch_steamcharts_timeseries, probe_steamdb]
