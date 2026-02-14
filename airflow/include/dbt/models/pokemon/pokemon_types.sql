{{ config(tags=["pokemon"]) }}

with types_ordered as (
  select
    pokemon_id,
    slot,
    type_name
  from {{ source('raw_pokemon', 'pokemon_types') }}
)

select
  pokemon_id,
  max(case when slot = 1 then type_name end) as primary_type,
  max(case when slot = 2 then type_name end) as secondary_type
from types_ordered
group by pokemon_id
