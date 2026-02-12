from datetime import datetime

from cosmos import DbtDag
from cosmos.config import ProfileConfig, ProjectConfig

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

profile_config = ProfileConfig(
    profile_name="airflow_agents_dbt",
    target_name="dev",
    profiles_yml_filepath=f"{DBT_DIR}/profiles.yml",
)

dbt_cosmos_dag = DbtDag(
    dag_id="dbt_cosmos_dag",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "postgres", "cosmos"],
    project_config=ProjectConfig(
        dbt_project_path=DBT_DIR,
        env_vars=DBT_ENV,
        install_dbt_deps=True,
    ),
    profile_config=profile_config,
)
