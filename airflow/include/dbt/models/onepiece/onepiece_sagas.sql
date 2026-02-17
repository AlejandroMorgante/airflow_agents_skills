{{ config(tags=["one-piece"]) }}

select
    id,
    cast(saga_number as integer)  as saga_number,
    title                         as saga_title,
    saga_chapitre                 as chapter_range,
    saga_volume                   as volume_range,
    saga_episode                  as episode_range,
    inserted_at
from {{ source('raw_onepiece', 'onepiece_sagas') }}
