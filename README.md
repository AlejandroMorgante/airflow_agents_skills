# Airflow + dbt Agent Challenge

> A hands-on technical challenge repository to evaluate AI coding agents (Codex, Claude, and others) on a realistic orchestration + analytics workflow.

---

## What This Repo Includes

This project provides a local environment where **Airflow (Astro Runtime)** orchestrates a **dbt + Postgres** pipeline.

- Airflow project under `airflow/`
- dbt project under `airflow/include/dbt`
- Dedicated Postgres service for dbt on `localhost:5433`
- API ingestion DAGs that fetch public data and load raw tables
- Cosmos DAGs that run dbt model subsets by tag (`open-meteo`, `steam`)

## Architecture at a Glance

```text
Public APIs -> Airflow DAGs -> Raw Postgres tables -> dbt models (analytics)
```

## Airflow DAGs and APIs 🚀

| DAG | Purpose | API(s) | Main output |
|---|---|---|---|
| `openmeteo_raw_ingest` | Ingest weather observations into raw layer | Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`) | `raw_openmeteo.openmeteo_hourly`, `raw_openmeteo.openmeteo_daily` |
| `steam_raw_ingest` | Ingest Steam catalog + player timeseries + source probes | Steam Store AppDetails API (`https://store.steampowered.com/api/appdetails`), SteamCharts chart-data (`https://steamcharts.com/app/<appid>/chart-data.json`), SteamDB probe (`https://steamdb.info/app/<appid>/charts/`) | `raw_steam.steam_app_list`, `raw_steam.steam_app_details`, `raw_steam.steamcharts_timeseries`, `raw_steam.steam_source_fetch_log` |
| `dbt_openmeteo_cosmos_dag` | Execute only Open-Meteo-tagged dbt models via Cosmos | No external API | `analytics.openmeteo_hourly`, `analytics.openmeteo_daily`, `analytics.openmeteo_daily_from_hourly`, `analytics.openmeteo_daily_quality` |
| `dbt_steam_cosmos_dag` | Execute only Steam-tagged dbt models via Cosmos | No external API | `analytics.steam_app_details`, `analytics.steam_focus_games`, `analytics.steam_monthly_players`, `analytics.steam_focus_games_monthly` |

## Data Models Produced 📊

### Core models

| Model/Table | Layer | Description |
|---|---|---|
| `analytics.raw_customers` | Seeded base | Seeded input customer data |
| `analytics.customer_summary` | Analytics | Clean projection of customer fields with typed `is_active` |

### Open-Meteo models

| Model/Table | Layer | Description |
|---|---|---|
| `raw_openmeteo.openmeteo_hourly` | Raw | Hourly weather block from Open-Meteo Forecast API |
| `raw_openmeteo.openmeteo_daily` | Raw | Daily weather block from Open-Meteo Forecast API |
| `analytics.openmeteo_hourly` | Analytics (tag: `open-meteo`) | Hourly normalized model with weather + geospatial metadata |
| `analytics.openmeteo_daily` | Analytics (tag: `open-meteo`) | Daily normalized model with max/min temperature and precipitation sum |
| `analytics.openmeteo_daily_from_hourly` | Analytics (tag: `open-meteo`) | Daily aggregates recomputed from hourly records |
| `analytics.openmeteo_daily_quality` | Analytics (tag: `open-meteo`) | Reconciliation model between API daily values and hourly-derived aggregates |

### Steam models

| Model/Table | Layer | Description |
|---|---|---|
| `raw_steam.steam_app_list` | Raw | Target app IDs list loaded by Airflow |
| `raw_steam.steam_app_details` | Raw | Latest app metadata snapshots from Steam Store API |
| `raw_steam.steamcharts_timeseries` | Raw | Historical concurrent players from SteamCharts |
| `raw_steam.steam_source_fetch_log` | Raw | Per-source fetch log (status, errors, payload snippets) |
| `analytics.steam_app_details` | Analytics (tag: `steam`) | Curated latest app details with typed pricing fields |
| `analytics.steam_focus_games` | Analytics (tag: `steam`) | Focus subset of selected games |
| `analytics.steam_monthly_players` | Analytics (tag: `steam`) | Monthly aggregated concurrent-player metrics |
| `analytics.steam_focus_games_monthly` | Analytics (tag: `steam`) | Focus game catalog joined with monthly metrics |

## Quick Start

### 1) Start the local stack

```bash
make start
```

### 2) Open Airflow UI

- URL: `http://localhost:8080`

### 3) Run the pipeline

- Trigger ingestion DAG(s): `openmeteo_raw_ingest` and/or `steam_raw_ingest`
- Trigger dbt DAG(s): `dbt_openmeteo_cosmos_dag` and/or `dbt_steam_cosmos_dag`

## Local dbt Commands (via Poetry)

```bash
make poetry-install
make dbt-compile
make dbt-seed
make dbt-run
make dbt-test
make dbt-all
```

## Inspect Data in DBeaver (or any SQL client)

Use this connection:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `dbt` |
| User | `dbt` |
| Password | `dbt` |
| Schema | `analytics` |

Useful tables/models:

- `analytics.raw_customers` (seed)
- `analytics.customer_summary` (model)
- `raw_openmeteo.openmeteo_hourly` (raw API ingestion)
- `raw_openmeteo.openmeteo_daily` (raw API ingestion, daily block)
- `analytics.openmeteo_hourly` (normalized weather model, hourly grain)
- `analytics.openmeteo_daily` (normalized weather model, daily grain)
- `analytics.openmeteo_daily_quality` (daily consistency checks)
- `raw_steam.steam_app_details` (Steam Store API raw snapshots)
- `raw_steam.steamcharts_timeseries` (SteamCharts raw history)
- `analytics.steam_monthly_players` (monthly aggregated player metrics)
- `analytics.steam_focus_games_monthly` (focus games + monthly metrics)

## Why Port 5433?

Airflow already uses its own Postgres metadata database. This project exposes dbt Postgres on **5433** to avoid collisions and keep responsibilities separate.

## Open-Meteo Data Contract

The `openmeteo_raw_ingest` DAG uses `https://api.open-meteo.com/v1/forecast` and stores two blocks:

1. `hourly` -> `raw_openmeteo.openmeteo_hourly`
2. `daily` -> `raw_openmeteo.openmeteo_daily`

### `raw_openmeteo.openmeteo_hourly` columns

| Column | Type | Description |
|---|---|---|
| `time` | `timestamptz` | Hourly timestamp from API |
| `temperature_2m` | `double precision` | Air temperature at 2m |
| `apparent_temperature` | `double precision` | Feels-like temperature |
| `relative_humidity_2m` | `double precision` | Relative humidity at 2m |
| `precipitation` | `double precision` | Hourly precipitation |
| `wind_speed_10m` | `double precision` | Wind speed at 10m |
| `weather_code` | `integer` | WMO weather condition code |
| `latitude` | `double precision` | Latitude of queried point |
| `longitude` | `double precision` | Longitude of queried point |
| `elevation` | `double precision` | Elevation in meters |
| `timezone` | `text` | Timezone returned by API |
| `timezone_abbreviation` | `text` | Timezone short name |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `(time, latitude, longitude)`.

### `raw_openmeteo.openmeteo_daily` columns

| Column | Type | Description |
|---|---|---|
| `date` | `date` | Daily date from API |
| `temperature_2m_max` | `double precision` | Daily max temperature |
| `temperature_2m_min` | `double precision` | Daily min temperature |
| `precipitation_sum` | `double precision` | Daily precipitation sum |
| `latitude` | `double precision` | Latitude of queried point |
| `longitude` | `double precision` | Longitude of queried point |
| `elevation` | `double precision` | Elevation in meters |
| `timezone` | `text` | Timezone returned by API |
| `timezone_abbreviation` | `text` | Timezone short name |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `(date, latitude, longitude)`.

### Configurable Airflow variables (Open-Meteo)

| Variable | Default | Purpose |
|---|---|---|
| `openmeteo_postgres_conn_id` | `postgres_default` | Target Postgres connection |
| `openmeteo_schema` | `raw_openmeteo` | Raw schema name |
| `openmeteo_hourly_table` | `openmeteo_hourly` | Raw hourly table name |
| `openmeteo_daily_table` | `openmeteo_daily` | Raw daily table name |
| `openmeteo_latitude` | `52.52` | Query latitude |
| `openmeteo_longitude` | `13.41` | Query longitude |
| `openmeteo_past_days` | `10` | Number of historic days requested |
| `openmeteo_hourly` | `temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,wind_speed_10m,weather_code` | Hourly variables requested to API |
| `openmeteo_daily` | `temperature_2m_max,temperature_2m_min,precipitation_sum` | Daily variables requested to API |

## Useful Make Targets

| Command | Purpose |
|---|---|
| `make start` | Start local Airflow services via Astro |
| `make stop` | Stop local services |
| `make restart` | Restart services |
| `make logs` | Stream Astro/Airflow logs |
| `make dbt-docs` | Generate and serve dbt docs (default port `8081`) |

---

## Notes

This repository is intentionally compact and practical. It is designed for fast iteration during agent evaluation, while still reflecting real-world orchestration and data transformation patterns.
