{{ config(materialized="incremental") }}

select
  '{{ run_started_at }}'::timestamp as run_started_at,
  '{{ invocation_id }}' as invocation_id
