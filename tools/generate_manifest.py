#!/usr/bin/env python
"""
ØYNA AI SYSTEM – MANIFEST GENERATOR

Bruk:
    cd tools
    python generate_manifest.py
    python generate_manifest.py --models-dir ../models --output ../manifest.json

Scriptet:
  * Skanner en katalog (default ../models) etter *.json
  * Leser hver modell-fil
  * Bygger én samlet manifest.json i prosjektroten
  * Er robust mot manglende felt (id, name, description, endpoints, schema)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_model_files(models_dir: Path) -> List[Path]:
    if not models_dir.exists():
        print(f"[WARN] Models directory not found: {models_dir}")
        return []
    return sorted(models_dir.rglob("*.json"))


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error in {path}: {e}")
    except OSError as e:
        print(f"[ERROR] Could not read {path}: {e}")
    return None


def extract_model_entry(path: Path, data: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """
    Forsøker å hente ut en fornuftig manifest-entry fra en enkelt modell-fil.

    Vi prøver flere varianter for id/navn siden vi ikke vet helt
    hvordan alle filer er strukturert ennå.
    """

    # Relative sti fra prosjektsrot – nyttig for debugging.
    try:
        rel_path = str(path.relative_to(project_root))
    except ValueError:
        # fallback hvis filen ligger utenfor prosjektet
        rel_path = str(path)

    # Forsøk å finne en ID
    model_id = (
        data.get("id")
        or data.get("model_id")
        or data.get("name")
        or path.stem  # fallback: filnavn uten .json
    )

    name = data.get("name") or model_id
    description = data.get("description") or data.get("summary") or ""

    # Endpoints kan være under flere nøkler – prøv litt fleksibelt
    endpoints = (
        data.get("endpoints")
        or data.get("tools")
        or data.get("operations")
        or []
    )

    # Schema kan hete litt forskjellig
    schema = (
        data.get("schema")
        or data.get("json_schema")
        or data.get("openapi_schema")
        or None
    )

    entry: Dict[str, Any] = {
        "id": model_id,
        "name": name,
        "description": description,
        "source_file": rel_path,
    }

    if endpoints:
        entry["endpoints"] = endpoints
    if schema is not None:
        entry["schema"] = schema

    return entry


def build_manifest(models_dir: Path, project_root: Path) -> Dict[str, Any]:
    files = find_model_files(models_dir)

    print(f"[INFO] Using models directory: {models_dir}")
    print(f"[INFO] Found {len(files)} JSON file(s).")

    models: List[Dict[str, Any]] = []

    for path in files:
        data = load_json(path)
        if data is None:
            continue

        entry = extract_model_entry(path, data, project_root)
        models.append(entry)

        print(f"  - Added model: {entry['id']}  (from {entry['source_file']})")

    manifest: Dict[str, Any] = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_count": len(models),
        "models": models,
    }

    return manifest


def parse_args(argv: List[str]) -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    default_models_dir = project_root / "models"
    default_output = project_root / "manifest.json"

    parser = argparse.ArgumentParser(
        description="Generate a consolidated manifest.json from model definition files."
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=default_models_dir,
        help=f"Directory containing model JSON files (default: {default_models_dir})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output manifest file (default: {default_output})",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    manifest = build_manifest(args.models_dir, project_root)

    # Sørg for at output-katalog finnes
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as f:
        if args.pretty:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        else:
            json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))

    print("")
    print(f"[INFO] Manifest written to: {args.output}")
    print(f"[INFO] Total models in manifest: {manifest['model_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
