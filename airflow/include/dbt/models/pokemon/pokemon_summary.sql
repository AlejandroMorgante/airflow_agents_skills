{{ config(tags=["pokemon"]) }}

with base_data as (
  select
    b.pokemon_id,
    b.pokemon_name,
    b.height_decimeters,
    b.weight_hectograms,
    b.base_experience,
    b.sprite_url,
    t.primary_type,
    t.secondary_type,
    s.hp,
    s.attack,
    s.defense,
    s.special_attack,
    s.special_defense,
    s.speed,
    s.total_stats
  from {{ ref('pokemon_base') }} b
  left join {{ ref('pokemon_types') }} t on b.pokemon_id = t.pokemon_id
  left join {{ ref('pokemon_stats') }} s on b.pokemon_id = s.pokemon_id
),

abilities_agg as (
  select
    pokemon_id,
    string_agg(ability_name, ', ' order by slot) as abilities,
    max(case when is_hidden then ability_name end) as hidden_ability,
    count(*) as ability_count
  from {{ ref('pokemon_abilities') }}
  group by pokemon_id
)

select
  bd.pokemon_id,
  bd.pokemon_name,
  bd.height_decimeters,
  bd.weight_hectograms,
  bd.base_experience,
  bd.sprite_url,
  bd.primary_type,
  bd.secondary_type,

  -- Type combination
  case
    when bd.secondary_type is not null then bd.primary_type || '/' || bd.secondary_type
    else bd.primary_type
  end as type_combination,

  -- Stats
  bd.hp,
  bd.attack,
  bd.defense,
  bd.special_attack,
  bd.special_defense,
  bd.speed,
  bd.total_stats,

  -- Power tier based on total stats
  case
    when bd.total_stats >= 600 then 'Legendary'
    when bd.total_stats >= 500 then 'Strong'
    when bd.total_stats >= 400 then 'Average'
    else 'Weak'
  end as power_tier,

  -- Attack style (physical vs special)
  case
    when bd.attack > bd.special_attack * 1.2 then 'Physical'
    when bd.special_attack > bd.attack * 1.2 then 'Special'
    else 'Balanced'
  end as attack_style,

  -- Battle role (offensive vs defensive)
  case
    when (bd.attack + bd.special_attack) > (bd.defense + bd.special_defense) * 1.2 then 'Offensive'
    when (bd.defense + bd.special_defense) > (bd.attack + bd.special_attack) * 1.2 then 'Defensive'
    else 'Balanced'
  end as battle_role,

  -- Speed tier
  case
    when bd.speed >= 100 then 'Very Fast'
    when bd.speed >= 70 then 'Fast'
    when bd.speed >= 50 then 'Average'
    else 'Slow'
  end as speed_tier,

  -- Abilities
  ab.abilities,
  ab.hidden_ability,
  ab.ability_count

from base_data bd
left join abilities_agg ab on bd.pokemon_id = ab.pokemon_id
