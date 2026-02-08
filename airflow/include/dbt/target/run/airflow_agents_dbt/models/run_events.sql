
      insert into "dbt"."analytics"."run_events" ("run_started_at", "invocation_id")
    (
        select "run_started_at", "invocation_id"
        from "run_events__dbt_tmp003757242585"
    )


  