create table if not exists {{ params.schema }}.{{ params.table }} (
  time timestamptz not null,
  temperature_2m double precision,
  apparent_temperature double precision,
  relative_humidity_2m double precision,
  precipitation double precision,
  wind_speed_10m double precision,
  weather_code integer,
  latitude double precision,
  longitude double precision,
  elevation double precision,
  timezone text,
  timezone_abbreviation text,
  inserted_at timestamptz not null default now(),
  primary key (time, latitude, longitude)
);

alter table {{ params.schema }}.{{ params.table }}
  add column if not exists apparent_temperature double precision,
  add column if not exists precipitation double precision,
  add column if not exists weather_code integer,
  add column if not exists elevation double precision,
  add column if not exists timezone text,
  add column if not exists timezone_abbreviation text;
