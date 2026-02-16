# Knowledge Base (Bedrock)

Esta carpeta contiene los documentos que puede consumir una Knowledge Base de Amazon Bedrock.

## Estructura

- `scripts/generate_kb_from_dbt.py`: genera documentos model-centric a partir de artifacts de dbt.
- `generated/docs/`: un documento por modelo (`model__*.md`) legible para humanos.
- `generated/docs/*.md.metadata.json`: metadata sidecar por documento en formato Bedrock S3.
- `generated/index.json`: indice de todos los documentos generados.

## Requisitos

1. Generar artifacts de dbt (al menos `manifest.json`):
   - `make dbt-compile` o `make dbt-docs-generate`
2. Ejecutar el generador:
   - `make kb-generate`

## Artefactos esperados

Por defecto el script busca:

- `airflow/include/dbt/target/manifest.json` (obligatorio)
- `airflow/include/dbt/target/catalog.json` (opcional)

## Diseno model-centric

Cada documento representa un modelo de dbt e incluye:

- columnas del modelo
- upstream models
- upstream sources (con columnas de source)
- downstream models
- tests asociados al modelo

## Salida para Bedrock

El output queda en `knowledge_base/generated/` y se puede subir al bucket S3 que use la KB:

- markdowns en `generated/docs/`
- sidecars `*.md.metadata.json` en `generated/docs/` (uno por markdown, mismo nombre + `.metadata.json`)
- `generated/index.json` con indice por documento (`by_document`)

## Uso en Bedrock

1. Subir `knowledge_base/generated/docs/` completo al prefijo S3 de la KB (markdown + sidecars `*.metadata.json`).
2. Configurar el data source de Bedrock para ingerir los markdowns.
