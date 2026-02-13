create table if not exists {{ params.schema }}.{{ params.table }} (
  time timestamptz not null,
  temperature_2m double precision,
  relative_humidity_2m double precision,
  wind_speed_10m double precision,
  latitude double precision,
  longitude double precision,
  inserted_at timestamptz not null default now(),
  primary key (time, latitude, longitude)
);
