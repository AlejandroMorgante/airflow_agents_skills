from datetime import datetime

from airflow.datasets import Dataset
from airflow.models import Variable
from cosmos import DbtDag
from cosmos.config import ProfileConfig, ProjectConfig, RenderConfig

DBT_DIR = "/usr/local/airflow/include/dbt"
ONEPIECE_RAW_READY = Dataset("airflow_agents://onepiece/raw_ready")
DBT_ENV = {
    "DBT_PROFILES_DIR": DBT_DIR,
    "DBT_HOST": Variable.get("dbt_host", default_var="host.docker.internal"),
    "DBT_PORT": Variable.get("dbt_port", default_var="5433"),
    "DBT_USER": Variable.get("dbt_user", default_var="dbt"),
    "DBT_PASSWORD": Variable.get("dbt_password", default_var="dbt"),
    "DBT_DBNAME": Variable.get("dbt_dbname", default_var="dbt"),
    "DBT_SCHEMA": Variable.get("dbt_schema", default_var="analytics"),
    "DBT_RAW_SCHEMA": Variable.get("onepiece_schema", default_var="raw_onepiece"),
}

profile_config = ProfileConfig(
    profile_name="airflow_agents_dbt",
    target_name="dev",
    profiles_yml_filepath=f"{DBT_DIR}/profiles.yml",
)

render_config = RenderConfig(select=["tag:one-piece"])


dbt_onepiece_cosmos_dag = DbtDag(
    dag_id="dbt_onepiece_cosmos_dag",
    schedule=[ONEPIECE_RAW_READY],
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "one-piece", "cosmos"],
    project_config=ProjectConfig(
        dbt_project_path=DBT_DIR,
        env_vars=DBT_ENV,
        install_dbt_deps=True,
    ),
    profile_config=profile_config,
    render_config=render_config,
)
