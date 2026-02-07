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

## Skill de PRs
La guia de buenas practicas para PRs vive en:
- `.codex/skills/pr-best-practices/SKILL.md`

Usa esa skill cuando alguien pida ayuda para preparar o redactar un PR.
