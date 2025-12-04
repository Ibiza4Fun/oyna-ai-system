#!/usr/bin/env python
"""
ØYNA AI SYSTEM – MODEL VALIDATOR

Validerer alle v1-modeller i models/v1 mot riktige JSON Schemas i models/schemas.

Bruk:
    cd tools
    python validate_models.py
    python validate_models.py --pretty

Exit-kode:
    0  = alle modeller er gyldige
    1  = minst én modell feilet validering
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft202012Validator, exceptions as js_exceptions


# -----------------------
# Utility-funksjoner
# -----------------------

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except js_exceptions.SchemaError as e:
        print(f"[ERROR] Invalid JSON Schema in {path}: {e}")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error in {path}: {e}")
    except OSError as e:
        print(f"[ERROR] Could not read {path}: {e}")
    return None


def discover_files(base: Path, subdir: str) -> List[Path]:
    root = base / subdir
    if not root.exists():
        print(f"[WARN] Directory not found: {root}")
        return []
    return sorted(root.glob("*.json"))


def detect_model_type(model_path: Path) -> Optional[str]:
    """Bestemmer modelltype ut fra filnavn.

    Konvensjon (per i dag):
      - *api_contract*          → api_contract
      - *digital_twin*          → digital_twin
      - *knowledge_graph*       → knowledge_graph
      - *master_system_model*   → master_system_model
      - *ai_master_manifest*    → manifest
    """

    name = model_path.stem.lower()

    if "api_contract" in name:
        return "api_contract"
    if "digital_twin" in name:
        return "digital_twin"
    if "knowledge_graph" in name:
        return "knowledge_graph"
    if "master_system_model" in name:
        return "master_system_model"
    if "ai_master_manifest" in name or ("manifest" in name and "schema" not in name):
        return "manifest"

    return None


def build_schema_index(schemas_dir: Path) -> Dict[str, Draft202012Validator]:
    # Forventede schema-filer
    expected: Dict[str, str] = {
        "api_contract": "api_contract_schema.json",
        "digital_twin": "digital_twin_schema.json",
        "knowledge_graph": "knowledge_graph_schema.json",
        "master_system_model": "master_system_model_schema.json",
        "manifest": "manifest_schema.json",
    }

    index: Dict[str, Draft202012Validator] = {}

    for key, filename in expected.items():
        schema_path = schemas_dir / filename
        if not schema_path.exists():
            print(f"[WARN] Schema file missing for '{key}': {schema_path}")
            continue

        data = load_json(schema_path)
        if data is None:
            continue

        try:
            validator = Draft202012Validator(data)
            index[key] = validator
            print(f"[INFO] Loaded schema for '{key}' from {schema_path}")
        except js_exceptions.SchemaError as e:
            print(f"[ERROR] Invalid JSON Schema in {schema_path}: {e}")

    return index


# -----------------------
# Valideringslogikk
# -----------------------

def validate_model(
    model_path: Path,
    model_data: Dict[str, Any],
    model_type: str,
    validators: Dict[str, Draft202012Validator],
) -> List[str]:
    errors: List[str] = []

    validator = validators.get(model_type)
    if validator is None:
        return [f"No schema loaded for model_type='{model_type}'"]

    for error in sorted(validator.iter_errors(model_data), key=lambda e: e.path):
        location = "/".join(str(p) for p in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")

    return errors


def run_validation(
    project_root: Path,
    pretty: bool = False,
) -> Tuple[int, int]:
    """Returnerer (antall_ok, antall_feil)."""

    models_dir = project_root / "models" / "v1"
    schemas_dir = project_root / "models" / "schemas"

    print(f"[INFO] Using models dir:  {models_dir}")
    print(f"[INFO] Using schemas dir: {schemas_dir}")

    model_files = discover_files(project_root / "models", "v1")
    if not model_files:
        print("[WARN] No model files found in models/v1")
        return 0, 0

    validators = build_schema_index(schemas_dir)

    ok = 0
    failed = 0

    print(f"[INFO] Found {len(model_files)} model file(s).\n")

    for model_path in model_files:
        rel = model_path.relative_to(project_root)
        model_type = detect_model_type(model_path)

        if model_type is None:
            print(f"[WARN] Skipping {rel} – could not infer model type from filename.")
            continue

        data = load_json(model_path)
        if data is None:
            failed += 1
            continue

        errors = validate_model(model_path, data, model_type, validators)

        if not errors:
            print(f"[OK]    {rel}  (type: {model_type})")
            ok += 1
        else:
            print(f"[FAIL]  {rel}  (type: {model_type})")
            failed += 1
            for msg in errors:
                if pretty:
                    print(f"       • {msg}")
                else:
                    print(f"       {msg}")

        print("")

    print("========== SUMMARY ==========")
    print(f"  Valid models  : {ok}")
    print(f"  Invalid models: {failed}")
    print("=============================")

    return ok, failed


# -----------------------
# CLI entrypoint
# -----------------------

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate v1 model JSON files against their schemas."
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print validation errors with bullets.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    ok, failed = run_validation(project_root, pretty=args.pretty)

    # Exit-code: 0 hvis alle er OK, 1 hvis noe feilet
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
