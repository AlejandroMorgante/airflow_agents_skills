# Airflow + dbt Agent Challenge

> A hands-on technical challenge repository to evaluate AI coding agents (Codex, Claude, and others) on a realistic orchestration + analytics workflow.

---

## What This Repo Includes

This project provides a local environment where **Airflow (Astro Runtime)** orchestrates a **dbt + Postgres** pipeline.

- Airflow project under `airflow/`
- dbt project under `airflow/include/dbt`
- Dedicated Postgres service for dbt on `localhost:5433`
- API ingestion DAGs that fetch public data and load raw tables
- Cosmos DAGs that run dbt model subsets by tag (`open-meteo`, `steam`, `pokemon`, `one-piece`)

## Architecture at a Glance

```text
Public APIs -> Airflow DAGs -> Raw Postgres tables -> dbt models (analytics)
```

## Airflow DAGs and APIs 🚀

| DAG | Purpose | API(s) | Main output |
|---|---|---|---|
| `openmeteo_raw_ingest` | Ingest weather observations into raw layer | Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`) | `raw_openmeteo.openmeteo_hourly`, `raw_openmeteo.openmeteo_daily` |
| `steam_raw_ingest` | Ingest Steam catalog + player timeseries + source probes | Steam Store AppDetails API (`https://store.steampowered.com/api/appdetails`), SteamCharts chart-data (`https://steamcharts.com/app/<appid>/chart-data.json`), SteamDB probe (`https://steamdb.info/app/<appid>/charts/`) | `raw_steam.steam_app_list`, `raw_steam.steam_app_details`, `raw_steam.steamcharts_timeseries`, `raw_steam.steam_source_fetch_log` |
| `pokemon_raw_ingest` | Ingest Pokemon data into normalized raw tables | PokeAPI (`https://pokeapi.co/api/v2/pokemon`) | `raw_pokemon.pokemon`, `raw_pokemon.pokemon_types`, `raw_pokemon.pokemon_stats`, `raw_pokemon.pokemon_abilities` |
| `onepiece_raw_ingest` | Ingest One Piece characters, devil fruits and sagas into raw tables | One Piece API (`https://api.api-onepiece.com/v2`) | `raw_onepiece.onepiece_characters`, `raw_onepiece.onepiece_fruits`, `raw_onepiece.onepiece_sagas` |
| `dbt_openmeteo_cosmos_dag` | Execute only Open-Meteo-tagged dbt models via Cosmos | No external API | `analytics.openmeteo_hourly`, `analytics.openmeteo_daily`, `analytics.openmeteo_daily_from_hourly`, `analytics.openmeteo_daily_quality` |
| `dbt_steam_cosmos_dag` | Execute only Steam-tagged dbt models via Cosmos | No external API | `analytics.steam_app_details`, `analytics.steam_focus_games`, `analytics.steam_monthly_players`, `analytics.steam_focus_games_monthly` |
| `dbt_pokemon_cosmos_dag` | Execute only Pokemon-tagged dbt models via Cosmos | No external API | `analytics.pokemon_base`, `analytics.pokemon_types`, `analytics.pokemon_stats`, `analytics.pokemon_abilities`, `analytics.pokemon_summary` |
| `dbt_onepiece_cosmos_dag` | Execute only One-Piece-tagged dbt models via Cosmos | No external API | `analytics.onepiece_characters`, `analytics.onepiece_fruits`, `analytics.onepiece_sagas`, `analytics.onepiece_summary` |

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

### Pokemon models

| Model/Table | Layer | Description |
|---|---|---|
| `raw_pokemon.pokemon` | Raw | Pokemon base data (id, name, height, weight, base_experience, sprite) |
| `raw_pokemon.pokemon_types` | Raw | Pokemon types (slot 1 = primary, slot 2 = secondary) |
| `raw_pokemon.pokemon_stats` | Raw | Pokemon base stats (HP, Attack, Defense, Special Attack, Special Defense, Speed) |
| `raw_pokemon.pokemon_abilities` | Raw | Pokemon abilities including hidden abilities |
| `analytics.pokemon_base` | Analytics (tag: `pokemon`) | Normalized Pokemon base table |
| `analytics.pokemon_types` | Analytics (tag: `pokemon`) | Types pivoted to primary_type and secondary_type columns |
| `analytics.pokemon_stats` | Analytics (tag: `pokemon`) | Stats pivoted to individual columns (hp, attack, defense, etc.) with total_stats |
| `analytics.pokemon_abilities` | Analytics (tag: `pokemon`) | Normalized abilities table |
| `analytics.pokemon_summary` | Analytics (tag: `pokemon`) | Complete Pokemon summary with calculated metrics (power_tier, attack_style, battle_role, speed_tier) |

### One Piece models

| Model/Table | Layer | Description |
|---|---|---|
| `raw_onepiece.onepiece_characters` | Raw | One Piece characters with crew and devil fruit references |
| `raw_onepiece.onepiece_fruits` | Raw | Devil fruits (Paramecia, Zoan, Logia, SMILE) with name, roman name and type |
| `raw_onepiece.onepiece_sagas` | Raw | Story sagas with chapter, volume and episode ranges |
| `analytics.onepiece_characters` | Analytics (tag: `one-piece`) | Normalized characters table with parsed size_cm, age_years and bounty_berries |
| `analytics.onepiece_fruits` | Analytics (tag: `one-piece`) | Devil fruits with normalized type_category (Paramecia / Zoan / Logia / SMILE) |
| `analytics.onepiece_sagas` | Analytics (tag: `one-piece`) | Sagas with parsed numeric saga_number |
| `analytics.onepiece_summary` | Analytics (tag: `one-piece`) | Complete character summary joined with devil fruit details, includes bounty_tier and crew_tier |

## Quick Start

### 1) Start the local stack

```bash
make start
```

### 2) Open Airflow UI

- URL: `http://localhost:8080`

### 3) Run the pipeline

- Trigger ingestion DAG(s): `openmeteo_raw_ingest` and/or `steam_raw_ingest` and/or `pokemon_raw_ingest` and/or `onepiece_raw_ingest`
- Trigger dbt DAG(s): `dbt_openmeteo_cosmos_dag` and/or `dbt_steam_cosmos_dag` and/or `dbt_pokemon_cosmos_dag` and/or `dbt_onepiece_cosmos_dag`

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
- `raw_pokemon.pokemon` (Pokemon base data from PokeAPI)
- `raw_pokemon.pokemon_stats` (Pokemon base stats raw data)
- `analytics.pokemon_summary` (complete Pokemon analytics with calculated metrics)
- `raw_onepiece.onepiece_characters` (One Piece characters raw data)
- `raw_onepiece.onepiece_fruits` (devil fruits raw data)
- `raw_onepiece.onepiece_sagas` (story sagas raw data)
- `analytics.onepiece_summary` (complete One Piece character analytics with bounty_tier and crew_tier)

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

## Pokemon Data Contract

The `pokemon_raw_ingest` DAG uses `https://pokeapi.co/api/v2/pokemon` and stores data in four normalized tables:

1. `pokemon` -> `raw_pokemon.pokemon`
2. `pokemon_types` -> `raw_pokemon.pokemon_types`
3. `pokemon_stats` -> `raw_pokemon.pokemon_stats`
4. `pokemon_abilities` -> `raw_pokemon.pokemon_abilities`

### `raw_pokemon.pokemon` columns

| Column | Type | Description |
|---|---|---|
| `id` | `integer` | Primary key, Pokemon ID from PokeAPI |
| `name` | `varchar(100)` | Pokemon name |
| `height` | `integer` | Pokemon height in decimeters |
| `weight` | `integer` | Pokemon weight in hectograms |
| `base_experience` | `integer` | Base experience yield |
| `sprite_front_default` | `text` | URL to default front sprite image |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `id`.

### `raw_pokemon.pokemon_types` columns

| Column | Type | Description |
|---|---|---|
| `pokemon_id` | `integer` | Pokemon ID (foreign key) |
| `slot` | `integer` | Type slot (1 = primary, 2 = secondary) |
| `type_name` | `varchar(50)` | Type name (e.g., fire, water, grass) |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `(pokemon_id, slot)`.

### `raw_pokemon.pokemon_stats` columns

| Column | Type | Description |
|---|---|---|
| `pokemon_id` | `integer` | Pokemon ID (foreign key) |
| `stat_name` | `varchar(50)` | Stat name (hp, attack, defense, special-attack, special-defense, speed) |
| `base_stat` | `integer` | Base stat value |
| `effort` | `integer` | Effort value (EVs) yielded when defeating this Pokemon |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `(pokemon_id, stat_name)`.

### `raw_pokemon.pokemon_abilities` columns

| Column | Type | Description |
|---|---|---|
| `pokemon_id` | `integer` | Pokemon ID (foreign key) |
| `slot` | `integer` | Ability slot number |
| `ability_name` | `varchar(100)` | Ability name |
| `is_hidden` | `boolean` | Whether this is a hidden ability |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `(pokemon_id, slot)`.

### Configurable Airflow variables (Pokemon)

| Variable | Default | Purpose |
|---|---|---|
| `pokemon_postgres_conn_id` | `postgres_default` | Target Postgres connection |
| `pokemon_schema` | `raw_pokemon` | Raw schema name |
| `pokemon_limit` | `500` | Number of Pokemon to fetch from API |
| `pokemon_max_workers` | `10` | Max concurrent threads for API fetching |

## One Piece Data Contract

The `onepiece_raw_ingest` DAG uses `https://api.api-onepiece.com/v2` and stores data in three tables:

1. `characters` -> `raw_onepiece.onepiece_characters`
2. `fruits` -> `raw_onepiece.onepiece_fruits`
3. `sagas` -> `raw_onepiece.onepiece_sagas`

### `raw_onepiece.onepiece_characters` columns

| Column | Type | Description |
|---|---|---|
| `id` | `integer` | Primary key, character ID from the API |
| `name` | `varchar(255)` | Character name |
| `size` | `varchar(50)` | Height as returned by the API (e.g. "174cm") |
| `age` | `varchar(50)` | Age as returned by the API (e.g. "19 ans") |
| `bounty` | `varchar(100)` | Bounty as returned by the API (e.g. "3.000.000.000") |
| `job` | `varchar(255)` | Role within the crew |
| `status` | `varchar(100)` | living / deceased / unknown |
| `crew_id` | `integer` | ID of the character's crew |
| `crew_name` | `varchar(255)` | Name of the crew |
| `crew_roman_name` | `varchar(255)` | Romanized crew name |
| `crew_status` | `varchar(100)` | Crew activity status |
| `crew_is_yonko` | `boolean` | Whether the crew is a Yonko crew |
| `fruit_id` | `integer` | ID of the devil fruit (nullable) |
| `fruit_name` | `varchar(255)` | Devil fruit name (nullable) |
| `fruit_roman_name` | `varchar(255)` | Devil fruit romanized name (nullable) |
| `fruit_type` | `varchar(100)` | Devil fruit type: Paramecia, Zoan, Logia, SMILE (nullable) |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `id`.

### `raw_onepiece.onepiece_fruits` columns

| Column | Type | Description |
|---|---|---|
| `id` | `integer` | Primary key, fruit ID from the API |
| `name` | `varchar(255)` | Fruit name |
| `roman_name` | `varchar(255)` | Romanized Japanese name (e.g. Gomu Gomu no Mi) |
| `type` | `varchar(100)` | Fruit type as returned by the API |
| `description` | `text` | Fruit power description |
| `image_url` | `text` | URL to fruit image |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `id`.

### `raw_onepiece.onepiece_sagas` columns

| Column | Type | Description |
|---|---|---|
| `id` | `integer` | Primary key, saga ID from the API |
| `title` | `varchar(255)` | Saga title (e.g. "East Blue") |
| `saga_number` | `varchar(10)` | Saga number as returned by the API |
| `saga_chapitre` | `varchar(100)` | Chapter range (e.g. "1 à 100") |
| `saga_volume` | `varchar(100)` | Volume range |
| `saga_episode` | `varchar(100)` | Episode range |
| `inserted_at` | `timestamptz` | Ingestion timestamp |

Primary key: `id`.

### Configurable Airflow variables (One Piece)

| Variable | Default | Purpose |
|---|---|---|
| `onepiece_postgres_conn_id` | `postgres_default` | Target Postgres connection |
| `onepiece_schema` | `raw_onepiece` | Raw schema name |
| `onepiece_language` | `en` | API language code |

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