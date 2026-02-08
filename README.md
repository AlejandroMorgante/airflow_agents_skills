airflow_agents_skills
=====================

Repositorio publico de desafio tecnico para probar agentes (Codex, Claude y otros).

Incluye un entorno local con:
- Airflow (Astro) en `airflow/`.
- dbt-postgres con un proyecto dbt en `airflow/include/dbt`.
- Una base Postgres separada para dbt (expuesta en `localhost:5433`).
- Un DAG `dbt_basic` que corre `dbt seed`, `dbt run` y `dbt test`.
- Un modelo incremental `run_events` que inserta una fila por corrida del DAG.

Arranque rapido
---------------

1) Levantar todo:

```
make start
```

2) Abrir Airflow:

```
http://localhost:8080
```

3) Ejecutar el DAG `dbt_basic`.

Ver datos en DBeaver
--------------------

Conectar a Postgres:
- Host: `localhost`
- Puerto: `5433`
- DB: `dbt`
- Usuario: `dbt`
- Password: `dbt`

Tablas:
- `analytics.run_events` (inserta una fila por corrida).
- `analytics.raw_customers` (seed).
- `analytics.customer_summary` (modelo).

Herramientas locales
--------------------

Para correr dbt local con Poetry:

```
make poetry-install
make dbt-compile
make dbt-run
make dbt-test
```
