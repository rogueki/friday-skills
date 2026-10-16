"""Validate onboarding metadata independently of Hermes runtime state."""

from __future__ import annotations

import json
import re

try:
    from scripts.build_registry import CAPABILITIES, ROOT
    from scripts.build_setup_catalog import build
except ModuleNotFoundError:  # direct scripts/validate.py invocation
    from build_registry import CAPABILITIES, ROOT
    from build_setup_catalog import build

STATUS = {"unknown"}  # Static package metadata has no live observation channel.
ACCOUNT = {"none", "required", "conditional"}
SCOPE_STATUS = {"unknown", "not_required"}
COST_MODEL = {"host_resources", "provider_usage", "subscription_license", "none", "unknown"}
SECRET = re.compile(r"(?i)(?:api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[^\s,'\"]{4,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")


def validate(catalog: dict) -> list[str]:
    errors = []
    if catalog.get("schema_version") != 2:
        errors.append("setup catalog schema_version must be 2")
    registry = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "registry/skill_capabilities.json").read_text(encoding="utf-8"))["skills"]
    names = {item["name"] for item in registry["skills"]}
    if catalog.get("inventory_count") != len(names) or set(catalog.get("skills", {})) != names:
        errors.append("setup catalog must cover exactly the registered skills")
    integrations = catalog.get("integrations", {})
    if not isinstance(integrations, dict) or not integrations:
        return errors + ["setup integrations missing"]
    for key, item in integrations.items():
        if not isinstance(item, dict) or item.get("account") not in ACCOUNT:
            errors.append(f"{key}: invalid account requirement")
            continue
        if not item.get("setup_de") or not item.get("settings_target"):
            errors.append(f"{key}: setup guidance or settings target missing")
        if item.get("auth_kind") not in {"none_or_optional", "provider_account", "local_session"}:
            errors.append(f"{key}: invalid authentication kind")
        permission = item.get("permissions")
        if not isinstance(permission, dict):
            errors.append(f"{key}: permission notice missing")
        else:
            required = permission.get("required_prerequisites")
            optional = permission.get("optional_prerequisites")
            if not isinstance(required, list) or not isinstance(optional, list):
                errors.append(f"{key}: required and optional permission prerequisites must be lists")
            else:
                for level, entries in (("required", required), ("optional", optional)):
                    for entry in entries:
                        if (not isinstance(entry, dict) or entry.get("status") != level
                                or not entry.get("kind") or not entry.get("notice")):
                            errors.append(f"{key}: invalid {level} permission prerequisite")
            if permission.get("scope_status") not in SCOPE_STATUS or not permission.get("scope_notice"):
                errors.append(f"{key}: invalid scope status or notice")
        cost = item.get("cost")
        if (not isinstance(cost, dict) or cost.get("model") not in COST_MODEL
                or not isinstance(cost.get("notice"), str) or not cost.get("notice")):
            errors.append(f"{key}: invalid cost notice")
        reference = item.get("reference")
        if not isinstance(reference, str) or not (ROOT / reference).is_file():
            errors.append(f"{key}: invalid reference")
    for name, item in catalog.get("skills", {}).items():
        if not isinstance(item, dict):
            errors.append(f"{name}: invalid record")
            continue
        for field in ("required_capabilities", "conditional_capabilities"):
            values = item.get(field)
            if not isinstance(values, list) or len(values) != len(set(values)) or set(values) - set(CAPABILITIES):
                errors.append(f"{name}: invalid {field}")
            if name in manifest and values != manifest[name][field.removesuffix("_capabilities")]:
                errors.append(f"{name}: capability manifest mismatch")
        for field in ("required_integrations", "conditional_integrations"):
            values = item.get(field)
            if not isinstance(values, list) or len(values) != len(set(values)) or set(values) - set(integrations):
                errors.append(f"{name}: invalid {field}")
        if set(item.get("required_integrations", [])) & set(item.get("conditional_integrations", [])):
            errors.append(f"{name}: integrations cannot be both required and conditional")
        if item.get("account") not in ACCOUNT or item.get("live_status") not in STATUS:
            errors.append(f"{name}: invalid account or live status")
        if not item.get("setup_de"):
            errors.append(f"{name}: setup guidance missing")
    if SECRET.search(json.dumps(catalog, ensure_ascii=False)):
        errors.append("setup catalog contains a possible secret value")
    compatibility = catalog.get("hermes_compatibility", {})
    for name in {"powerpoint", "computer-use", "obsidian", "opencode", "codex", "claude-code", "telephony"}:
        item = compatibility.get(name, {})
        if (item.get("distribution") not in {"bundled", "not_bundled"}
                or item.get("installed_status") != "unknown"
                or item.get("friday_requirement") != "optional"
                or not str(item.get("official_url", "")).startswith("https://hermes-agent.nousresearch.com/docs/")):
            errors.append(f"{name}: invalid Hermes compatibility reference")
    if catalog != build():
        errors.append("setup catalog differs from generated source")
    return errors


if __name__ == "__main__":
    catalog = json.loads((ROOT / "registry/integration_setup.json").read_text(encoding="utf-8"))
    failures = validate(catalog)
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"setup catalog valid: {len(catalog['skills'])} skills")
