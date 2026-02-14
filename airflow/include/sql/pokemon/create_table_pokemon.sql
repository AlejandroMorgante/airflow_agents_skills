create table if not exists {{ params.schema }}.pokemon (
  id integer primary key,
  name varchar(100) not null,
  height integer,
  weight integer,
  base_experience integer,
  sprite_front_default text,
  inserted_at timestamptz not null default now()
);

create index if not exists idx_pokemon_name on {{ params.schema }}.pokemon(name);
