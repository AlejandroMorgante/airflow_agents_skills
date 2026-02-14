create table if not exists {{ params.schema }}.pokemon_types (
  pokemon_id integer not null,
  slot integer not null,
  type_name varchar(50) not null,
  inserted_at timestamptz not null default now(),
  primary key (pokemon_id, slot)
);

create index if not exists idx_pokemon_types_type_name on {{ params.schema }}.pokemon_types(type_name);
