create table if not exists {{ params.schema }}.pokemon_abilities (
  pokemon_id integer not null,
  slot integer not null,
  ability_name varchar(100) not null,
  is_hidden boolean not null default false,
  inserted_at timestamptz not null default now(),
  primary key (pokemon_id, slot)
);

create index if not exists idx_pokemon_abilities_ability_name on {{ params.schema }}.pokemon_abilities(ability_name);
create index if not exists idx_pokemon_abilities_is_hidden on {{ params.schema }}.pokemon_abilities(is_hidden);
