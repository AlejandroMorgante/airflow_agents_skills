{{ config(tags=["open-meteo"]) }}

select
  cast(time as timestamptz) as observed_at,
  cast(time as date) as observed_date,
  cast(temperature_2m as double precision) as temperature_2m,
  cast(apparent_temperature as double precision) as apparent_temperature,
  cast(relative_humidity_2m as double precision) as relative_humidity_2m,
  cast(precipitation as double precision) as precipitation,
  cast(wind_speed_10m as double precision) as wind_speed_10m,
  cast(weather_code as integer) as weather_code,
  cast(latitude as double precision) as latitude,
  cast(longitude as double precision) as longitude,
  cast(elevation as double precision) as elevation,
  cast(timezone as text) as timezone,
  cast(timezone_abbreviation as text) as timezone_abbreviation
from {{ source('raw_openmeteo', 'openmeteo_hourly') }}
