{% docs __overview__ %}
# Airflow + dbt con ingestas API y trazabilidad para agentes

Este proyecto implementa un flujo end-to-end donde Airflow ingiere datos de APIs publicas y dbt construye una capa analitica pensada para consumo humano y por agentes.

## Arquitectura

1. DAGs de ingesta (`*_raw_ingest`) consultan APIs externas y cargan tablas `raw_*`.
2. DAGs Cosmos (`dbt_*_cosmos_dag`) ejecutan subsets de dbt por tags.
3. Modelos `analytics` tipan, estandarizan y agregan datos para analisis.

## Open-Meteo

- Ingesta desde `https://api.open-meteo.com/v1/forecast`.
- Carga dos bloques de API:
  - `hourly` -> `raw_openmeteo.openmeteo_hourly`
  - `daily` -> `raw_openmeteo.openmeteo_daily`
- Orquestacion:
  - `openmeteo_raw_ingest` publica dataset `airflow_agents://openmeteo/raw_ready`
  - `dbt_openmeteo_cosmos_dag` corre modelos con tag `open-meteo`
- Modelos principales:
  - `openmeteo_hourly`: normalizacion horaria con metadata de ubicacion y timezone.
  - `openmeteo_daily`: normalizacion diaria desde bloque `daily`.
  - `openmeteo_daily_from_hourly`: agregado diario calculado desde hourly.
  - `openmeteo_daily_quality`: reconciliacion API daily vs agregado hourly.

## Steam

- Ingesta desde fuentes Steam:
  - Steam Store AppDetails API: `https://store.steampowered.com/api/appdetails?appids=<appid>`
  - SteamCharts chart-data: `https://steamcharts.com/app/<appid>/chart-data.json`
  - SteamDB probe: `https://steamdb.info/app/<appid>/charts/`
- Capa raw generada por `steam_raw_ingest`:
  - `raw_steam.steam_app_list`
  - `raw_steam.steam_app_details`
  - `raw_steam.steamcharts_timeseries`
  - `raw_steam.steam_source_fetch_log`
- Orquestacion:
  - `steam_raw_ingest` publica dataset `airflow_agents://steam/raw_ready`
  - `dbt_steam_cosmos_dag` se dispara por ese dataset y ejecuta solo `tag:steam`
- Modelos principales:
  - `steam_app_details`: ultimo estado exitoso por app con tipado de precios.
  - `steam_focus_games`: subset de apps foco para analisis.
  - `steam_monthly_players`: agregados mensuales de concurrencia desde SteamCharts.
  - `steam_focus_games_monthly`: join entre catalogo foco y metricas mensuales.

## Pokemon

- Ingesta desde `https://pokeapi.co/api/v2/pokemon`.
- Carga datos normalizados en cuatro tablas:
  - `raw_pokemon.pokemon`: datos base (id, nombre, altura, peso, experiencia, sprite)
  - `raw_pokemon.pokemon_types`: tipos (slot 1 = primario, slot 2 = secundario)
  - `raw_pokemon.pokemon_stats`: stats base (HP, Attack, Defense, Special Attack, Special Defense, Speed)
  - `raw_pokemon.pokemon_abilities`: habilidades incluyendo habilidades ocultas
- Orquestacion:
  - `pokemon_raw_ingest` publica dataset `airflow_agents://pokemon/raw_ready`
  - `dbt_pokemon_cosmos_dag` se dispara por ese dataset y ejecuta solo `tag:pokemon`
- Modelos principales:
  - `pokemon_base`: tabla base normalizada de Pokemon
  - `pokemon_types`: tipos pivoteados a columnas primary_type y secondary_type
  - `pokemon_stats`: stats pivoteados a columnas individuales (hp, attack, defense, etc.) con total_stats
  - `pokemon_abilities`: tabla normalizada de habilidades
  - `pokemon_summary`: resumen completo con metricas calculadas (power_tier, attack_style, battle_role, speed_tier)

## Convenciones para agentes

- Las fuentes raw se consumen siempre por `source()`.
- Los modelos intermedios/analiticos se consumen por `ref()`.
- El naming explicita granularidad (`hourly`, `daily`, `monthly`) y objetivo (`quality`, `summary`, `focus`).
- Los tags organizan modelos por dominio: `open-meteo`, `steam`, `pokemon`.
- Las columnas clave de trazabilidad en Open-Meteo son:
  - tiempo: `observed_at`, `observed_date`
  - geografia: `latitude`, `longitude`, `elevation`
  - contexto temporal: `timezone`, `timezone_abbreviation`
- Las columnas clave de trazabilidad en Steam son:
  - identificador: `appid` / `app_id`
  - tiempo de carga/observacion: `ingested_at`, `observed_at`, `month`
  - auditoria de fuentes: `source`, `endpoint`, `status_code`, `ok`, `error_message`
- Las columnas clave de trazabilidad en Pokemon son:
  - identificador: `pokemon_id`
  - nombre: `pokemon_name`
  - clasificacion: `type_combination`, `power_tier`
  - metricas: `total_stats`, `attack_style`, `battle_role`, `speed_tier`

Para explorar linaje, empezar en:
- `models/openmeteo/schema.yml`
- `models/steam/schema.yml`
- `models/pokemon/schema.yml`
y seguir dependencias por `ref()`.
{% enddocs %}
