#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    return cleaned.strip("-") or "unknown"


def detect_domain(name: str, tags: list[str]) -> str:
    low = name.lower()
    tag_set = {t.lower() for t in tags}
    if "open-meteo" in tag_set or "openmeteo" in low:
        return "openmeteo"
    if "steam" in tag_set or "steam" in low:
        return "steam"
    if "pokemon" in tag_set or "pokemon" in low:
        return "pokemon"
    return "general"


def clean_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def merge_columns(base_columns: dict[str, Any], catalog_columns: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(base_columns)
    if not catalog_columns:
        return merged

    for key, value in catalog_columns.items():
        existing = merged.get(key, {})
        merged[key] = {**existing, **value}
    return merged


@dataclass
class DocRecord:
    doc_id: str
    relative_doc_path: str
    relative_metadata_path: str
    resource_type: str
    domain: str
    name: str
    schema: str
    tags: list[str]
    checksum: str


def write_doc(
    out_docs_dir: Path,
    resource_type: str,
    name_hint: str,
    content: str,
    metadata: dict[str, Any],
) -> DocRecord:
    filename = f"{resource_type}__{slugify(name_hint)}.md"
    doc_path = out_docs_dir / filename

    doc_path.write_text(content, encoding="utf-8")
    metadata_path = doc_path.with_name(f"{doc_path.name}.metadata.json")
    bedrock_metadata = {
        "metadataAttributes": build_bedrock_metadata_attributes(metadata),
    }
    metadata_path.write_text(json.dumps(bedrock_metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    checksum = sha256(content.encode("utf-8")).hexdigest()
    return DocRecord(
        doc_id=slugify(f"{resource_type}_{name_hint}"),
        relative_doc_path=str(doc_path),
        relative_metadata_path=str(metadata_path),
        resource_type=resource_type,
        domain=clean_text(metadata.get("domain"), "general"),
        name=clean_text(metadata.get("name"), "unknown"),
        schema=clean_text(metadata.get("schema"), "unknown"),
        tags=[str(t) for t in (metadata.get("tags") or [])],
        checksum=checksum,
    )


def build_bedrock_metadata_attributes(metadata: dict[str, Any]) -> dict[str, Any]:
    tags = [clean_text(t) for t in (metadata.get("tags") or []) if clean_text(t)]
    attrs = {
        "resource_type": clean_text(metadata.get("resource_type"), "unknown"),
        "domain": clean_text(metadata.get("domain"), "general"),
        "schema": clean_text(metadata.get("schema"), "unknown"),
        "name": clean_text(metadata.get("name"), "unknown"),
        "unique_id": clean_text(metadata.get("unique_id"), "unknown"),
        "tags": tags,
        "tag_count": len(tags),
        "upstream_model_count": int(metadata.get("upstream_model_count") or 0),
        "upstream_source_count": int(metadata.get("upstream_source_count") or 0),
        "downstream_model_count": int(metadata.get("downstream_model_count") or 0),
        "associated_test_count": int(metadata.get("associated_test_count") or 0),
    }
    for tag in tags:
        attrs[f"tag_{slugify(tag)}"] = True
    return attrs


def build_model_centric_doc(
    model: dict[str, Any],
    source_map: dict[str, dict[str, Any]],
    node_map: dict[str, dict[str, Any]],
    tests_by_model_id: dict[str, list[dict[str, Any]]],
    child_map: dict[str, list[str]],
) -> tuple[str, dict[str, Any]]:
    name = clean_text(model.get("name"), "unknown_model")
    schema = clean_text(model.get("schema"), "unknown_schema")
    description = clean_text(model.get("description"), "Sin descripcion.")
    tags = model.get("tags") or []
    unique_id = clean_text(model.get("unique_id"), "")

    depends_on = (model.get("depends_on") or {}).get("nodes") or []
    upstream_models = [dep for dep in depends_on if dep.startswith("model.")]
    upstream_sources = [dep for dep in depends_on if dep.startswith("source.")]

    downstream_raw = child_map.get(unique_id, []) if unique_id else []
    downstream_models = [dep for dep in downstream_raw if dep.startswith("model.")]

    columns = model.get("columns") or {}
    related_tests = tests_by_model_id.get(unique_id, [])

    lines = [
        f"# Model `{schema}.{name}`",
        "",
        "## Overview",
        description,
        "",
        "## Technical Metadata",
        f"- Resource type: `model`",
        f"- Unique id: `{unique_id}`",
        f"- Schema: `{schema}`",
        f"- Name: `{name}`",
        f"- Tags: `{', '.join(tags) if tags else 'none'}`",
        "",
    ]

    lines.extend(["## Columns", ""])
    if columns:
        for col_name, col_info in sorted(columns.items()):
            col_desc = clean_text(col_info.get("description"), "Sin descripcion.")
            data_type = clean_text(col_info.get("data_type"), "unknown")
            lines.append(f"- `{col_name}` (`{data_type}`): {col_desc}")
    else:
        lines.append("- No columns metadata found.")
    lines.append("")

    lines.extend(["## Upstream Models", ""])
    if upstream_models:
        for dep in sorted(upstream_models):
            dep_node = node_map.get(dep, {})
            dep_schema = clean_text(dep_node.get("schema"), "unknown")
            dep_name = clean_text(dep_node.get("name"), dep)
            lines.append(f"- `{dep_schema}.{dep_name}` ({dep})")
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Upstream Sources", ""])
    if upstream_sources:
        for dep in sorted(upstream_sources):
            src = source_map.get(dep, {})
            src_schema = clean_text(src.get("schema"), "unknown")
            src_source_name = clean_text(src.get("source_name"), "unknown")
            src_table = clean_text(src.get("name"), dep)
            src_desc = clean_text(src.get("description"), "Sin descripcion.")
            lines.append(f"- `{src_schema}.{src_table}` (source `{src_source_name}`): {src_desc}")

            src_columns = src.get("columns") or {}
            if src_columns:
                lines.append("  - Source columns:")
                for col_name, col_info in sorted(src_columns.items()):
                    col_desc = clean_text(col_info.get("description"), "Sin descripcion.")
                    data_type = clean_text(col_info.get("data_type"), "unknown")
                    lines.append(f"    - `{col_name}` (`{data_type}`): {col_desc}")
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Downstream Models", ""])
    if downstream_models:
        for dep in sorted(downstream_models):
            dep_node = node_map.get(dep, {})
            dep_schema = clean_text(dep_node.get("schema"), "unknown")
            dep_name = clean_text(dep_node.get("name"), dep)
            lines.append(f"- `{dep_schema}.{dep_name}` ({dep})")
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Associated Tests", ""])
    if related_tests:
        for test_node in sorted(related_tests, key=lambda t: clean_text(t.get("name"), "")):
            test_name = clean_text(test_node.get("name"), "unknown_test")
            test_unique_id = clean_text(test_node.get("unique_id"), "")
            test_column = clean_text(test_node.get("column_name"), "n/a")
            test_meta = test_node.get("test_metadata") or {}
            generic_name = clean_text(test_meta.get("name"), "generic_test")
            kwargs = test_meta.get("kwargs") or {}
            lines.append(f"- `{test_name}` ({test_unique_id})")
            lines.append(f"  - Generic test: `{generic_name}`")
            lines.append(f"  - Column: `{test_column}`")
            if kwargs:
                lines.append("  - Arguments:")
                for key, value in sorted(kwargs.items()):
                    lines.append(f"    - `{key}`: `{value}`")
    else:
        lines.append("- None")
    lines.append("")

    content = "\n".join(lines).strip() + "\n"

    metadata = {
        "resource_type": "model",
        "schema": schema,
        "name": name,
        "unique_id": unique_id,
        "tags": tags,
        "domain": detect_domain(name, tags),
        "upstream_model_count": len(upstream_models),
        "upstream_source_count": len(upstream_sources),
        "downstream_model_count": len(downstream_models),
        "associated_test_count": len(related_tests),
    }
    return content, metadata


def index_tests_by_model(node_map: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    tests_by_model_id: dict[str, list[dict[str, Any]]] = {}
    for node in node_map.values():
        if node.get("resource_type") != "test":
            continue

        depends_on = (node.get("depends_on") or {}).get("nodes") or []
        model_targets = [dep for dep in depends_on if dep.startswith("model.")]
        for model_id in model_targets:
            tests_by_model_id.setdefault(model_id, []).append(node)

    return tests_by_model_id


def clear_docs_dir(out_docs_dir: Path) -> None:
    if not out_docs_dir.exists():
        return
    for pattern in ("*.md", "*.md.metadata.json"):
        for file in out_docs_dir.glob(pattern):
            file.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate model-centric markdown KB docs from dbt artifacts.")
    parser.add_argument(
        "--manifest",
        default="airflow/include/dbt/target/manifest.json",
        help="Path to dbt manifest.json",
    )
    parser.add_argument(
        "--catalog",
        default="airflow/include/dbt/target/catalog.json",
        help="Path to dbt catalog.json (optional)",
    )
    parser.add_argument(
        "--out-dir",
        default="knowledge_base/generated",
        help="Output directory for docs and metadata",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found: {manifest_path}")

    manifest = read_json(manifest_path)
    catalog_path = Path(args.catalog)
    catalog = read_json(catalog_path) if catalog_path.exists() else {}

    node_map = manifest.get("nodes") or {}
    source_map = manifest.get("sources") or {}
    child_map = manifest.get("child_map") or {}

    out_dir = Path(args.out_dir)
    out_docs_dir = out_dir / "docs"
    out_docs_dir.mkdir(parents=True, exist_ok=True)
    clear_docs_dir(out_docs_dir)
    for legacy_dir in ("metadata", "bedrock_docs"):
        legacy_path = out_dir / legacy_dir
        if legacy_path.exists() and legacy_path.is_dir():
            for child in legacy_path.glob("*"):
                if child.is_file():
                    child.unlink()
            legacy_path.rmdir()

    tests_by_model_id = index_tests_by_model(node_map)

    records: list[DocRecord] = []

    for node in node_map.values():
        if node.get("resource_type") != "model":
            continue

        unique_id = clean_text(node.get("unique_id"), "")
        catalog_node = ((catalog.get("nodes") or {}).get(unique_id)) if catalog else None
        node["columns"] = merge_columns(node.get("columns") or {}, (catalog_node or {}).get("columns"))

        # Merge source columns from catalog, so source details included in model docs are typed.
        depends_on = (node.get("depends_on") or {}).get("nodes") or []
        for dep in depends_on:
            if not dep.startswith("source."):
                continue
            source_node = source_map.get(dep)
            if not source_node:
                continue
            catalog_source = ((catalog.get("sources") or {}).get(dep)) if catalog else None
            source_node["columns"] = merge_columns(
                source_node.get("columns") or {},
                (catalog_source or {}).get("columns"),
            )

        content, metadata = build_model_centric_doc(node, source_map, node_map, tests_by_model_id, child_map)
        name_hint = f"{node.get('schema', 'analytics')}_{node.get('name', 'unknown')}"
        records.append(write_doc(out_docs_dir, "model", name_hint, content, metadata))

    by_document = {record.doc_id: record.__dict__ for record in records}
    index = {
        "generator": "knowledge_base/scripts/generate_kb_from_dbt.py",
        "mode": "model_centric",
        "manifest_path": str(manifest_path),
        "catalog_path": str(catalog_path) if catalog_path.exists() else None,
        "document_count": len(records),
        "documents": [record.__dict__ for record in records],
        "by_document": by_document,
    }
    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Generated {len(records)} model documents in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
