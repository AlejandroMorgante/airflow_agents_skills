{{ config(tags=["one-piece"]) }}

select
    id,
    name,
    -- Parse height to numeric cm (e.g. "174cm" -> 174)
    nullif(regexp_replace(size, '[^0-9]', '', 'g'), '')::integer   as size_cm,
    -- Parse age to numeric (e.g. "19 ans" -> 19)
    nullif(regexp_replace(age, '[^0-9]', '', 'g'), '')::integer    as age_years,
    -- Normalize bounty: strip dots/spaces and cast to bigint
    nullif(regexp_replace(bounty, '[^0-9]', '', 'g'), '')::bigint  as bounty_berries,
    bounty                                                          as bounty_raw,
    job,
    status,
    crew_id,
    crew_name,
    crew_roman_name,
    crew_status,
    crew_is_yonko,
    fruit_id,
    fruit_name,
    fruit_roman_name,
    fruit_type,
    inserted_at
from {{ source('raw_onepiece', 'onepiece_characters') }}
