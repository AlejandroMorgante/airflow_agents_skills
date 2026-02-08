---
name: airflow_agents_skills
description: Instrucciones y decisiones de configuracion del repositorio.
---

# Configuracion del repositorio

Fecha: 7 de febrero de 2026.

## Proteccion de rama (`main`)
Se activo proteccion de rama con estas reglas:
- Requiere al menos 1 aprobacion de review para mergear PRs.
- No se requieren status checks por el momento.
- `enforce_admins` esta desactivado, por lo que los administradores pueden mergear sin aprobacion.

Nota: En repos personales GitHub no permite listas de bypass por usuario. Si mas adelante queres exigir aprobacion tambien para admins, activamos `enforce_admins=true`.

## Descripcion del repositorio (GitHub)
Se seteo la descripcion para indicar que es un desafio tecnico para probar agentes (Codex, Claude y otros).

## Skill de PRs
La guia de buenas practicas para PRs vive en:
- `.codex/skills/pr-best-practices/SKILL.md`

Usa esa skill cuando alguien pida ayuda para preparar o redactar un PR.

# Cambios recientes (setup Airflow + dbt)

Fecha: 8 de febrero de 2026.

## Estructura y tooling
- Proyecto Astro (Airflow) en `airflow/`.
- `Makefile` en la raiz con targets para `astro dev` y comandos dbt via Poetry.
- `airflow/pyproject.toml` con `dbt-postgres==1.10.0`.

## Base de datos dbt
- Servicio `dbt-postgres` en `airflow/docker-compose.override.yml`.
- Puerto host `5433` para evitar conflicto con la metadata DB de Airflow.

## dbt project
- Proyecto dbt en `airflow/include/dbt` (models + seeds + schema tests).
- Modelo incremental `run_events` que inserta una fila por corrida.
- `profiles.yml` parametrizado por env vars.

## DAG
- `dbt_basic` separado en `dbt_seed` -> `dbt_run` -> `dbt_test`.
- Variables de conexion dbt fijadas en el DAG.
- Host de dbt configurado a `host.docker.internal:5433` para evitar problemas DNS.
