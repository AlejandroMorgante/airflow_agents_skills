{{ config(tags=["pokemon"]) }}

select
  pokemon_id,
  slot,
  ability_name,
  is_hidden
from {{ source('raw_pokemon', 'pokemon_abilities') }}
