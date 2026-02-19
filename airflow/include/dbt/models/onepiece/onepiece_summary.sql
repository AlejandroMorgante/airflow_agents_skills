{{ config(tags=["one-piece"]) }}

with characters as (
    select * from {{ ref('onepiece_characters') }}
),

fruits as (
    select * from {{ ref('onepiece_fruits') }}
),

fruits_agg as (
    -- one row per character_fruit_id for the join
    select
        id              as fruit_id,
        name            as fruit_name,
        roman_name      as fruit_roman_name,
        type_category   as fruit_type_category,
        description     as fruit_description
    from fruits
)

select
    c.id                as character_id,
    c.name              as character_name,
    c.size_cm,
    c.age_years,
    c.bounty_berries,
    c.bounty_raw,
    c.job,
    c.status,

    -- Crew info
    c.crew_id,
    c.crew_name,
    c.crew_roman_name,
    c.crew_is_yonko,

    -- Devil fruit info
    f.fruit_id,
    f.fruit_name,
    f.fruit_roman_name,
    f.fruit_type_category,
    case when f.fruit_id is not null then true else false end as has_devil_fruit,

    -- Bounty tier
    case
        when c.bounty_berries >= 1000000000 then 'Yonko-tier (1B+)'
        when c.bounty_berries >= 500000000  then 'Emperor-class (500M+)'
        when c.bounty_berries >= 100000000  then 'Supernova (100M+)'
        when c.bounty_berries >= 10000000   then 'Notable Pirate (10M+)'
        when c.bounty_berries > 0           then 'Low Bounty'
        else 'No Bounty'
    end as bounty_tier,

    -- Crew tier
    case
        when c.crew_is_yonko is true then 'Yonko Crew'
        when c.crew_id is not null   then 'Regular Crew'
        else 'No Crew / Unknown'
    end as crew_tier,

    c.inserted_at

from characters c
left join fruits_agg f on c.fruit_id = f.fruit_id
