create table if not exists {{ params.schema }}.{{ params.source_fetch_log_table }} (
  id bigserial primary key,
  source text not null,
  endpoint text not null,
  appid bigint,
  status_code integer,
  ok boolean not null default false,
  error_message text,
  payload jsonb,
  fetched_at timestamptz not null default now()
);
