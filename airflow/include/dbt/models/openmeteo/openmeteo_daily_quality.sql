{{ config(tags=["open-meteo"]) }}

select
  d.observed_date,
  d.latitude,
  d.longitude,
  d.temperature_2m_max,
  h.temperature_2m_max_from_hourly,
  d.temperature_2m_min,
  h.temperature_2m_min_from_hourly,
  d.precipitation_sum,
  h.precipitation_sum_from_hourly,
  (d.temperature_2m_max - h.temperature_2m_max_from_hourly) as delta_max_temp,
  (d.temperature_2m_min - h.temperature_2m_min_from_hourly) as delta_min_temp,
  (d.precipitation_sum - h.precipitation_sum_from_hourly) as delta_precipitation_sum,
  h.hourly_samples
from {{ ref('openmeteo_daily') }} d
left join {{ ref('openmeteo_daily_from_hourly') }} h
  on d.observed_date = h.observed_date
 and d.latitude = h.latitude
 and d.longitude = h.longitude
