"""Validate this package without third-party dependencies or network access."""

from pathlib import Path
import json
import re
import sys

from build_registry import build
from build_setup_catalog import build as build_setup_catalog
from validate_setup_catalog import validate as validate_setup_catalog

ROOT = Path(__file__).resolve().parents[1]

try:
    import yaml  # Optional: use the installed YAML parser for full frontmatter syntax checks.
except ImportError:
    yaml = None


def validate() -> list[str]:
    errors: list[str] = []
    try:
        setup = json.loads((ROOT / "registry/integration_setup.json").read_text(encoding="utf-8"))
        errors.extend(validate_setup_catalog(setup))
        if setup != build_setup_catalog():
            errors.append("integration setup catalog out of date")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"integration setup catalog missing or invalid: {exc}")
    registry = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
    names = [entry["name"] for entry in registry["skills"]]
    if len(names) != len(set(names)):
        errors.append("registry contains duplicate skill names")
    paths = sorted((ROOT / "skills").rglob("SKILL.md"))
    if len(paths) != len(names):
        errors.append(f"expected {len(names)} skills; found {len(paths)}")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not match:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        front = match.group(1)
        if yaml is not None:
            try:
                metadata = yaml.safe_load(front)
                if not isinstance(metadata, dict):
                    raise ValueError("frontmatter must be a mapping")
            except (yaml.YAMLError, ValueError) as exc:
                errors.append(f"{path}: invalid YAML frontmatter: {exc}")
                continue
            name = metadata.get("name")
        else:
            name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", front, re.M)
            name = name_match.group(1) if name_match else None
            if front.count("metadata:") != 1 or front.count("  hermes:") != 1:
                errors.append(f"{path}: invalid metadata/hermes frontmatter structure")
        if name != path.parent.name or name not in names:
            errors.append(f"{path}: name/folder/registry mismatch")
        for key in ("description", "version", "author", "license"):
            if yaml is not None:
                present = bool(metadata.get(key))
            else:
                present = bool(re.search(rf"^{key}:\s*\S+", front, re.M))
            if not present:
                errors.append(f"{path}: missing {key}")
        if yaml is not None and not isinstance(metadata.get("metadata", {}).get("hermes", {}).get("tags"), list):
            errors.append(f"{path}: metadata.hermes.tags must be a list")
        if (yaml is not None and (metadata.get("author") != "RogueKI" or metadata.get("license") != "MIT")) or (yaml is None and ("RogueKI" not in front or "MIT" not in front)):
            errors.append(f"{path}: author/license mismatch")
        body = text[match.end():].lower()
        for token in ("use", "do not", "inputs", "mode", "capability", "output", "verif"):
            if token not in body:
                errors.append(f"{path}: missing operational concept {token}")
    for schema in (ROOT / "shared/schemas").glob("*.json"):
        json.loads(schema.read_text(encoding="utf-8"))
    roadmap = json.loads((ROOT / "registry/roadmap.json").read_text(encoding="utf-8"))
    planned = roadmap["skills"]
    if len(planned) != roadmap["plan_total"] or len({x["plan_name"] for x in planned}) != len(planned) or len({x["section"] for x in planned}) != len(planned):
        errors.append("roadmap count or unique names/sections invalid")
    mapped = {x["plan_name"]: x for x in planned}
    for entry in registry["skills"]:
        legacy = entry.get("legacy_plan_name")
        if legacy and (legacy not in mapped or mapped[legacy]["status"] != "implemented" or mapped[legacy]["implemented_name"] != entry["name"]):
            errors.append(f"registry/roadmap mismatch: {entry['name']}")
    for item in planned:
        if item["status"] not in {"planned", "implemented"}:
            errors.append(f"invalid roadmap status: {item['plan_name']}")
        if item["status"] == "implemented" and item["implemented_name"] not in names:
            errors.append(f"roadmap implementation missing: {item['plan_name']}")
        if item["status"] == "planned" and item["implemented_name"] is not None:
            errors.append(f"roadmap planned entry has implementation: {item['plan_name']}")
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for name in ("MEMORY.md", "SCOPE.md", "JARVIS_HERMES_SKILLS_IMPLEMENTIERUNGSPLAN_CODEX.md", ".env"):
        if name not in ignored:
            errors.append(f".gitignore missing {name}")
    for filename, expected in build().items():
        path = ROOT / "registry" / filename
        if not path.is_file():
            errors.append(f"missing operational registry: {filename}")
        else:
            try:
                actual = json.loads(path.read_text(encoding="utf-8"))
                if actual != expected:
                    errors.append(f"operational registry out of date: {filename}")
            except json.JSONDecodeError as exc:
                errors.append(f"invalid registry {filename}: {exc}")
    for path in (ROOT / "fixtures").rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid fixture {path}: {exc}")
    for path in (ROOT / "skills").rglob("tests/cases.json"):
        try:
            cases = json.loads(path.read_text(encoding="utf-8"))
            if cases.get("skill") != path.parents[1].name:
                errors.append(f"test case skill mismatch: {path}")
            seen = {case.get("id") for case in cases.get("cases", [])}
            if not {"positive", "negative", "collision"}.issubset(seen):
                errors.append(f"missing routing test cases: {path}")
            for case in cases.get("cases", []):
                if case.get("expected") not in {"select", "reject", "defer"} or not case.get("request"):
                    errors.append(f"invalid routing test case: {path}")
        except (json.JSONDecodeError, AttributeError, TypeError) as exc:
            errors.append(f"invalid test cases {path}: {exc}")
    for skill_path in paths:
        if not (skill_path.parent / "tests/cases.json").is_file():
            errors.append(f"missing routing test cases: {skill_path.parent.name}")
    for path in ROOT.rglob("*"):
        if any(part in {".git", "__pycache__", "artifacts"} for part in path.relative_to(ROOT).parts):
            continue
        if path.is_symlink():
            errors.append(f"symlink in package: {path}")
    return errors


if __name__ == "__main__":
    issues = validate()
    if issues:
        print("\n".join(issues), file=sys.stderr)
        raise SystemExit(1)
    print(f"OK: {len(list((ROOT / 'skills').rglob('SKILL.md')))} skills, registry, roadmap, schemas and exclusions validated")
