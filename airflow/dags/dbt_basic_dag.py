from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

DBT_DIR = "/usr/local/airflow/include/dbt"
DBT_ENV = {
    "DBT_PROFILES_DIR": DBT_DIR,
    # Use host.docker.internal to avoid DNS issues between containers.
    "DBT_HOST": "host.docker.internal",
    "DBT_PORT": "5433",
    "DBT_USER": "dbt",
    "DBT_PASSWORD": "dbt",
    "DBT_DBNAME": "dbt",
    "DBT_SCHEMA": "analytics",
}


with DAG(
    dag_id="dbt_basic",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["dbt", "postgres"],
) as dag:
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {DBT_DIR} && dbt seed",
        env=DBT_ENV,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run",
        env=DBT_ENV,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test",
        env=DBT_ENV,
    )

    dbt_seed >> dbt_run >> dbt_test
