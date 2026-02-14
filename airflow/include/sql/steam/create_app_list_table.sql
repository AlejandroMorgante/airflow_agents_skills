create table if not exists {{ params.schema }}.{{ params.app_list_table }} (
  appid bigint primary key,
  name text,
  ingested_at timestamptz not null default now()
);
