{{ config(tags=["pokemon"]) }}

select
  cast(id as integer) as pokemon_id,
  cast(name as varchar(100)) as pokemon_name,
  cast(height as integer) as height_decimeters,
  cast(weight as integer) as weight_hectograms,
  cast(base_experience as integer) as base_experience,
  cast(sprite_front_default as text) as sprite_url
from {{ source('raw_pokemon', 'pokemon') }}
