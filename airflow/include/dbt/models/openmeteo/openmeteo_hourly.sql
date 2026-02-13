{{ config(tags=["open-meteo"]) }}

select
  cast(time as timestamptz) as observed_at,
  cast(temperature_2m as double precision) as temperature_2m,
  cast(relative_humidity_2m as double precision) as relative_humidity_2m,
  cast(wind_speed_10m as double precision) as wind_speed_10m,
  cast(latitude as double precision) as latitude,
  cast(longitude as double precision) as longitude
from {{ source('raw_openmeteo', 'openmeteo_hourly') }}
