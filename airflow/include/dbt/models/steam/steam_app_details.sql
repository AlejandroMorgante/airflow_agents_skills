{{ config(tags=["steam"]) }}

with latest as (
  select
    appid,
    success,
    status_code,
    type,
    name,
    is_free,
    required_age,
    price_overview,
    developers,
    publishers,
    categories,
    genres,
    release_date,
    payload,
    ingested_at,
    row_number() over (partition by appid order by ingested_at desc) as rn
  from {{ source('raw_steam', 'steam_app_details') }}
)
select
  cast(appid as bigint) as app_id,
  name as app_name,
  type as app_type,
  cast(coalesce(is_free, false) as boolean) as is_free,
  cast(required_age as integer) as required_age,
  cast(price_overview ->> 'initial' as integer) as price_initial_cents,
  cast(price_overview ->> 'final' as integer) as price_final_cents,
  cast(price_overview ->> 'discount_percent' as integer) as discount_percent,
  price_overview ->> 'currency' as price_currency,
  status_code,
  developers,
  publishers,
  categories,
  genres,
  release_date,
  payload,
  ingested_at
from latest
where rn = 1
  and success = true
