select
  customer_id,
  first_name,
  last_name,
  is_active::boolean as is_active
from {{ ref('raw_customers') }}
