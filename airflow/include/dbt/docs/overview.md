{% docs __overview__ %}
# Airflow + dbt con ingestas API y trazabilidad para agentes

Este proyecto implementa un flujo end-to-end donde Airflow ingiere datos de APIs publicas y dbt construye una capa analitica pensada para consumo humano y por agentes.

## Arquitectura

1. DAGs de ingesta (`*_raw_ingest`) consultan APIs externas y cargan tablas `raw_*`.
2. DAGs Cosmos (`dbt_*_cosmos_dag`) ejecutan subsets de dbt por tags.
3. Modelos `analytics` tipan, estandarizan y agregan datos para analisis.

## Open-Meteo (estado actual)

- Ingesta desde `https://api.open-meteo.com/v1/forecast`.
- Carga dos bloques de API:
  - `hourly` -> `raw_openmeteo.openmeteo_hourly`
  - `daily` -> `raw_openmeteo.openmeteo_daily`
- Modelos principales:
  - `openmeteo_hourly`: normalizacion horaria con metadata de ubicacion y timezone.
  - `openmeteo_daily`: normalizacion diaria desde bloque `daily`.
  - `openmeteo_daily_from_hourly`: agregado diario calculado desde hourly.
  - `openmeteo_daily_quality`: reconciliacion API daily vs agregado hourly.

## Steam

- Ingesta desde multiples fuentes:
  - Steam Store API: `https://store.steampowered.com/api/appdetails`
  - SteamCharts: `https://steamcharts.com/app/<appid>/chart-data.json`
  - SteamDB: `https://steamdb.info/app/<appid>/charts/`
- Carga datos en:
  - `raw_steam.steam_app_list`: lista de app IDs objetivo
  - `raw_steam.steam_app_details`: metadatos de apps desde Steam Store API
  - `raw_steam.steamcharts_timeseries`: series temporales de jugadores concurrentes
  - `raw_steam.steam_source_fetch_log`: log de fetches por fuente
- Modelos principales:
  - `steam_app_details`: detalles de apps curados con tipado de precios
  - `steam_focus_games`: subset enfocado de juegos seleccionados
  - `steam_monthly_players`: metricas mensuales de jugadores concurrentes
  - `steam_focus_games_monthly`: catalogo de juegos enfocados con metricas mensuales

## Pokemon

- Ingesta desde `https://pokeapi.co/api/v2/pokemon`.
- Carga datos normalizados en cuatro tablas:
  - `raw_pokemon.pokemon`: datos base (id, nombre, altura, peso, experiencia, sprite)
  - `raw_pokemon.pokemon_types`: tipos (slot 1 = primario, slot 2 = secundario)
  - `raw_pokemon.pokemon_stats`: stats base (HP, Attack, Defense, Special Attack, Special Defense, Speed)
  - `raw_pokemon.pokemon_abilities`: habilidades incluyendo habilidades ocultas
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
- Las columnas clave de trazabilidad varian por dominio:
  - **Open-Meteo**: `observed_at`, `observed_date`, `latitude`, `longitude`, `timezone`
  - **Steam**: `app_id`, `name`, `fetched_at`, `month`
  - **Pokemon**: `pokemon_id`, `pokemon_name`, `type_combination`, `total_stats`

Para explorar linaje:
- Open-Meteo: empezar en `models/openmeteo/schema.yml`
- Steam: empezar en `models/steam/schema.yml`
- Pokemon: empezar en `models/pokemon/schema.yml`

Todos siguen dependencias por `ref()`.
{% enddocs %}
