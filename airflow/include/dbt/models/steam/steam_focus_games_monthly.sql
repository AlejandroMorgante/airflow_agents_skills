{{ config(tags=["steam"]) }}

select
  f.app_id,
  f.app_name,
  f.app_type,
  f.is_free,
  f.price_currency,
  f.price_final_cents,
  m.month,
  m.avg_concurrent_players,
  m.peak_concurrent_players,
  m.samples_in_month
from {{ ref('steam_focus_games') }} as f
join {{ ref('steam_monthly_players') }} as m
  on f.app_id = m.app_id
