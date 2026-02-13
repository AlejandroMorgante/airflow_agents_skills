AIRFLOW_DIR := airflow
DBT_DIR := $(AIRFLOW_DIR)/include/dbt
AIRFLOW_DIR_ABS := $(abspath $(AIRFLOW_DIR))
POETRY := poetry
DBT_LOCAL_ENV := DBT_PROJECT_DIR=$(abspath $(DBT_DIR)) DBT_PROFILES_DIR=$(abspath $(DBT_DIR)) DBT_HOST=localhost DBT_PORT=5433 DBT_USER=dbt DBT_PASSWORD=dbt DBT_DBNAME=dbt DBT_SCHEMA=analytics
DBT_DOCS_PORT ?= 8081

.PHONY: start stop restart logs poetry-install dbt-compile dbt-seed dbt-run dbt-test dbt-all dbt-docs-generate dbt-docs

start:
	cd $(AIRFLOW_DIR) && astro dev start

stop:
	cd $(AIRFLOW_DIR) && astro dev stop

restart:
	cd $(AIRFLOW_DIR) && astro dev restart

logs:
	cd $(AIRFLOW_DIR) && astro dev logs

poetry-install:
	$(POETRY) -C $(AIRFLOW_DIR_ABS) install

dbt-compile:
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt compile

dbt-seed:
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt seed

dbt-run:
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt run

dbt-test:
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt test

dbt-all:
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt seed
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt run
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt test

dbt-docs-generate:
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt docs generate

dbt-docs:
	$(MAKE) dbt-docs-generate
	$(DBT_LOCAL_ENV) $(POETRY) -C $(AIRFLOW_DIR_ABS) run dbt docs serve --port $(DBT_DOCS_PORT)
