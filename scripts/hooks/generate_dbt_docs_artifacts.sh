#!/usr/bin/env bash
set -euo pipefail

make dbt-docs-generate

git add \
  airflow/include/dbt/target/index.html \
  airflow/include/dbt/target/manifest.json \
  airflow/include/dbt/target/catalog.json
