{{ config(tags=["open-meteo"]) }}

select
  cast(date as date) as observed_date,
  cast(temperature_2m_max as double precision) as temperature_2m_max,
  cast(temperature_2m_min as double precision) as temperature_2m_min,
  cast(precipitation_sum as double precision) as precipitation_sum,
  cast(latitude as double precision) as latitude,
  cast(longitude as double precision) as longitude,
  cast(elevation as double precision) as elevation,
  cast(timezone as text) as timezone,
  cast(timezone_abbreviation as text) as timezone_abbreviation
from {{ source('raw_openmeteo', 'openmeteo_daily') }}
