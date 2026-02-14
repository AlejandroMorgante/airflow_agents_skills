{{ config(tags=["pokemon"]) }}

with stats_pivoted as (
  select
    pokemon_id,
    max(case when stat_name = 'hp' then base_stat end) as hp,
    max(case when stat_name = 'attack' then base_stat end) as attack,
    max(case when stat_name = 'defense' then base_stat end) as defense,
    max(case when stat_name = 'special-attack' then base_stat end) as special_attack,
    max(case when stat_name = 'special-defense' then base_stat end) as special_defense,
    max(case when stat_name = 'speed' then base_stat end) as speed
  from {{ source('raw_pokemon', 'pokemon_stats') }}
  group by pokemon_id
)

select
  pokemon_id,
  hp,
  attack,
  defense,
  special_attack,
  special_defense,
  speed,
  (hp + attack + defense + special_attack + special_defense + speed) as total_stats
from stats_pivoted
