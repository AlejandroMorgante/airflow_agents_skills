{{ config(tags=["open-meteo"]) }}

select
  observed_date,
  latitude,
  longitude,
  min(temperature_2m) as temperature_2m_min_from_hourly,
  max(temperature_2m) as temperature_2m_max_from_hourly,
  sum(coalesce(precipitation, 0.0)) as precipitation_sum_from_hourly,
  avg(temperature_2m) as temperature_2m_avg_from_hourly,
  avg(apparent_temperature) as apparent_temperature_avg_from_hourly,
  avg(relative_humidity_2m) as relative_humidity_avg_from_hourly,
  avg(wind_speed_10m) as wind_speed_10m_avg_from_hourly,
  count(*) as hourly_samples
from {{ ref('openmeteo_hourly') }}
group by 1, 2, 3
