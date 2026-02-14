create table if not exists {{ params.schema }}.{{ params.table }} (
  date date not null,
  temperature_2m_max double precision,
  temperature_2m_min double precision,
  precipitation_sum double precision,
  latitude double precision,
  longitude double precision,
  elevation double precision,
  timezone text,
  timezone_abbreviation text,
  inserted_at timestamptz not null default now(),
  primary key (date, latitude, longitude)
);
