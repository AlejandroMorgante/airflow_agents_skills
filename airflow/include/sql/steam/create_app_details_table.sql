create table if not exists {{ params.schema }}.{{ params.app_details_table }} (
  appid bigint primary key,
  success boolean not null default false,
  status_code integer,
  type text,
  name text,
  is_free boolean,
  required_age integer,
  price_overview jsonb,
  developers jsonb,
  publishers jsonb,
  categories jsonb,
  genres jsonb,
  release_date jsonb,
  payload jsonb,
  ingested_at timestamptz not null default now()
);

alter table {{ params.schema }}.{{ params.app_details_table }}
  add column if not exists price_overview jsonb;
