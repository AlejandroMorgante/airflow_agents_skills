{{ config(tags=["one-piece"]) }}

select
    id,
    name,
    roman_name,
    type,
    case
        when type ilike '%Logia%'     then 'Logia'
        when type ilike '%Mythique%'
          or type ilike '%Mythic%'    then 'Mythic Zoan'
        when type ilike '%Antique%'
          or type ilike '%Ancient%'   then 'Ancient Zoan'
        when type ilike '%Zoan%'      then 'Zoan'
        when type ilike '%Paramecia%' then 'Paramecia'
        when type ilike '%Smile%'     then 'SMILE'
        else 'Unknown'
    end as type_category,
    description,
    image_url,
    inserted_at
from {{ source('raw_onepiece', 'onepiece_fruits') }}
