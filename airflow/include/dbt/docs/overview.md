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

## Convenciones para agentes

- Las fuentes raw se consumen siempre por `source()`.
- Los modelos intermedios/analiticos se consumen por `ref()`.
- El naming explicita granularidad (`hourly`, `daily`) y objetivo (`quality`).
- Las columnas clave de trazabilidad en Open-Meteo son:
  - tiempo: `observed_at`, `observed_date`
  - geografia: `latitude`, `longitude`, `elevation`
  - contexto temporal: `timezone`, `timezone_abbreviation`

Para explorar linaje, empezar en `models/openmeteo/schema.yml` y seguir dependencias por `ref()`.
{% enddocs %}
