{{ config(tags=["steam"]) }}

with base as (
  select
    cast(appid as bigint) as app_id,
    date_trunc('month', observed_at)::date as month,
    cast(concurrent_players as integer) as concurrent_players
  from {{ source('raw_steam', 'steamcharts_timeseries') }}
  where source = 'steamcharts'
)
select
  app_id,
  month,
  avg(concurrent_players)::numeric(18,2) as avg_concurrent_players,
  max(concurrent_players) as peak_concurrent_players,
  min(concurrent_players) as min_concurrent_players,
  count(*) as samples_in_month
from base
group by 1, 2
