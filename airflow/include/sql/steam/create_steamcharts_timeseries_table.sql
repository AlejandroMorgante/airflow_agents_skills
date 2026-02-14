create table if not exists {{ params.schema }}.{{ params.steamcharts_timeseries_table }} (
  source text not null,
  appid bigint not null,
  observed_at timestamptz not null,
  concurrent_players integer,
  ingested_at timestamptz not null default now(),
  primary key (source, appid, observed_at)
);
