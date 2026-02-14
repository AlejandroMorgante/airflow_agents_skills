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
| `openmeteo_raw_ingest` | Ingest weather observations into raw layer | Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`) | `raw_openmeteo.openmeteo_hourly` |
| `steam_raw_ingest` | Ingest Steam catalog + player timeseries + source probes | Steam Store AppDetails API (`https://store.steampowered.com/api/appdetails`), SteamCharts chart-data (`https://steamcharts.com/app/<appid>/chart-data.json`), SteamDB probe (`https://steamdb.info/app/<appid>/charts/`) | `raw_steam.steam_app_list`, `raw_steam.steam_app_details`, `raw_steam.steamcharts_timeseries`, `raw_steam.steam_source_fetch_log` |
| `dbt_openmeteo_cosmos_dag` | Execute only Open-Meteo-tagged dbt models via Cosmos | No external API | `analytics.openmeteo_hourly` |
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
| `raw_openmeteo.openmeteo_hourly` | Raw | Hourly weather data loaded by Airflow ingestion DAG |
| `analytics.openmeteo_hourly` | Analytics (tag: `open-meteo`) | Normalized weather model with typed timestamps and numeric metrics |

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
- `analytics.openmeteo_hourly` (normalized weather model)
- `raw_steam.steam_app_details` (Steam Store API raw snapshots)
- `raw_steam.steamcharts_timeseries` (SteamCharts raw history)
- `analytics.steam_monthly_players` (monthly aggregated player metrics)
- `analytics.steam_focus_games_monthly` (focus games + monthly metrics)

## Why Port 5433?

Airflow already uses its own Postgres metadata database. This project exposes dbt Postgres on **5433** to avoid collisions and keep responsibilities separate.

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
