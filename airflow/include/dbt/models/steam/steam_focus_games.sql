{{ config(tags=["steam"]) }}

select
  app_id,
  app_name,
  app_type,
  is_free,
  price_initial_cents,
  price_final_cents,
  discount_percent,
  price_currency,
  required_age,
  status_code,
  developers,
  publishers,
  categories,
  genres,
  release_date,
  payload,
  ingested_at
from {{ ref('steam_app_details') }}
where app_id in (10, 562810, 2383760)
