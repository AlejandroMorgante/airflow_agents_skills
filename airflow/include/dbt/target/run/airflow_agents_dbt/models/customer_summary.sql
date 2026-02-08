
  
    

  create  table "dbt"."analytics"."customer_summary__dbt_tmp"
  
  
    as
  
  (
    select
  customer_id,
  first_name,
  last_name,
  is_active::boolean as is_active
from "dbt"."analytics"."raw_customers"
  );
  