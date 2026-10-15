"""Filesystem-level smoke check; does not certify Hermes or a live adapter."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
skills = registry["skills"]
missing = [item["name"] for item in skills if not (ROOT / item["path"]).is_file()]
if missing:
    raise SystemExit(f"missing skill files: {missing}")
print(f"OK: {len(skills)} registered skill files available; Hermes discovery and live adapters not tested")
