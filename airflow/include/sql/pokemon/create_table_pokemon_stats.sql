create table if not exists {{ params.schema }}.pokemon_stats (
  pokemon_id integer not null,
  stat_name varchar(50) not null,
  base_stat integer not null,
  effort integer not null,
  inserted_at timestamptz not null default now(),
  primary key (pokemon_id, stat_name)
);

create index if not exists idx_pokemon_stats_stat_name on {{ params.schema }}.pokemon_stats(stat_name);
