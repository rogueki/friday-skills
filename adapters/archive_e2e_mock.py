"""In-memory-only E2E6 archive composition over pinned synthetic file contents."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import PurePosixPath
import re
import unicodedata
from typing import Any

from shared.policy import action_fingerprint, risk_tier
from shared.runtime import MockRuntime, dashboard_mapping, load_fixture


VARIANTS = frozenset({
    "default", "bad_hash", "mock_approved", "missing_source", "unreadable_source",
    "path_escape", "collision", "insufficient_capacity", "missing_backup",
    "stale_approval", "mismatched_approval", "denied_approval", "replayed_approval",
    "corrupt_target", "partial_copy",
})
APPROVAL_VARIANTS = frozenset({
    "mock_approved", "stale_approval", "mismatched_approval", "denied_approval",
    "replayed_approval", "corrupt_target", "partial_copy",
})
RESERVED = frozenset({"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                      *(f"lpt{i}" for i in range(1, 10))})


class ArchiveMockError(ValueError):
    def __init__(self, code: str, *, invalid_ids: list[str] | None = None):
        super().__init__(code)
        self.code = code
        self.invalid_ids = invalid_ids or []


def _safe_path(value: Any, root: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value or ":" in value:
        raise ArchiveMockError("unsafe_path")
    normalized = unicodedata.normalize("NFC", value)
    parts = normalized.split("/")
    if (parts[0] != root or len(parts) < 2 or any(
        part in {"", ".", ".."} or part.endswith((".", " "))
        or part.split(".", 1)[0].casefold() in RESERVED for part in parts
    ) or len(normalized) > 240):
        raise ArchiveMockError("unsafe_path")
    return str(PurePosixPath(*parts))


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def _inventory(source: dict[str, Any], trace: list[str]) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    rows: list[dict[str, Any]] = []
    contents: dict[str, bytes] = {}
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    invalid: list[str] = []
    for item in source["files"]:
        file_id = item["id"]
        if not isinstance(file_id, str) or not re.fullmatch(r"[a-z0-9_-]+", file_id) or file_id in seen_ids:
            raise ArchiveMockError("invalid_source_identity")
        seen_ids.add(file_id)
        path = _safe_path(item["path"], source["source_root"])
        if path.casefold() in seen_paths:
            raise ArchiveMockError("source_collision")
        seen_paths.add(path.casefold())
        if item.get("readable") is not True or not isinstance(item.get("content"), str):
            invalid.append(file_id)
            continue
        data = item["content"].encode("utf-8")
        digest = _sha(data)
        if digest != item.get("sha256"):
            invalid.append(file_id)
            continue
        if not re.fullmatch(r"20\d\d", str(item.get("year", ""))):
            raise ArchiveMockError("invalid_year")
        rows.append({"id": file_id, "source": path, "size": len(data), "sha256": digest,
                     "year": item["year"], "target_override": item.get("target_override")})
        contents[file_id] = data
    trace.extend(["read_only_synthetic_scan", "sha256_inventory"])
    if invalid:
        raise ArchiveMockError("integrity_failure", invalid_ids=invalid)
    if not rows:
        raise ArchiveMockError("empty_inventory")
    return rows, contents


def _groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str], list[str]] = defaultdict(list)
    for row in rows:
        groups[(row["size"], row["sha256"])].append(row["id"])
    return [{"sha256": digest, "size": size, "ids": sorted(ids), "method": "byte_sha256"}
            for (size, digest), ids in sorted(groups.items()) if len(ids) > 1]


def _manifest(source: dict[str, Any], rows: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    target_root = source["target_root"]
    free_bytes = source["destination_free_bytes"]
    backup = source["backup"]
    if (backup.get("verified") is not True or not backup.get("snapshot_id")
            or datetime.fromisoformat(backup["observed_at"].replace("Z", "+00:00")) > now
            or now - datetime.fromisoformat(backup["observed_at"].replace("Z", "+00:00")) > timedelta(days=1)):
        raise ArchiveMockError("backup_unverified")
    if type(free_bytes) is not int or free_bytes < 0:
        raise ArchiveMockError("capacity_unknown")
    entries: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for row in rows:
        intended = row["target_override"] or f"{target_root}/{row['year']}/{row['id']}-{PurePosixPath(row['source']).name}"
        target = _safe_path(intended, target_root)
        if target.casefold() in seen_targets:
            raise ArchiveMockError("target_collision")
        seen_targets.add(target.casefold())
        entries.append({"id": row["id"], "source": row["source"], "target": target,
                        "operation": "copy_only_no_overwrite", "size": row["size"],
                        "sha256": row["sha256"], "rollback": {"remove_new_copy_only": target,
                        "source_preserved": True}})
    total_bytes = sum(entry["size"] for entry in entries)
    required_bytes = total_bytes * 2  # destination plus temporary copy overhead
    if free_bytes < required_bytes:
        raise ArchiveMockError("insufficient_capacity")
    manifest = {"type": "synthetic_copy_manifest", "source_root": source["source_root"],
                "target_root": target_root, "entries": entries, "file_count": len(entries),
                "source_bytes": total_bytes, "required_free_bytes": required_bytes,
                "destination_free_bytes": free_bytes, "backup": backup,
                "overwrite": False, "delete_originals": False}
    return manifest


def _mock_approval(manifest: dict[str, Any], variant: str, now: datetime) -> dict[str, Any]:
    manifest_hash = action_fingerprint("archive_copy", manifest["target_root"], manifest)
    approval = {"kind": "simulated_test_grant_only", "status": "approved",
                "fingerprint": manifest_hash, "manifest_hash": manifest_hash,
                "target": manifest["target_root"], "tier": risk_tier("archive_copy"),
                "expires_at": (now + timedelta(minutes=5)).isoformat(),
                "idempotency_key": f"synthetic-{manifest_hash[:16]}", "used": False}
    if variant == "stale_approval":
        approval["expires_at"] = (now - timedelta(seconds=1)).isoformat()
    elif variant == "mismatched_approval":
        approval["manifest_hash"] = "0" * 64
    elif variant == "denied_approval":
        approval["status"] = "denied"
    elif variant == "replayed_approval":
        approval["used"] = True
    return approval


def _verify_mock_grant(approval: dict[str, Any], manifest: dict[str, Any], now: datetime) -> None:
    digest = action_fingerprint("archive_copy", manifest["target_root"], manifest)
    if (approval.get("kind") != "simulated_test_grant_only" or approval.get("status") != "approved"
            or approval.get("fingerprint") != digest or approval.get("manifest_hash") != digest
            or approval.get("target") != manifest["target_root"] or approval.get("tier") != 2
            or approval.get("idempotency_key") != f"synthetic-{digest[:16]}"):
        raise ArchiveMockError("mock_approval_mismatch")
    if approval.get("used") is True:
        raise ArchiveMockError("mock_approval_replayed")
    expiry = datetime.fromisoformat(approval["expires_at"])
    if expiry <= now:
        raise ArchiveMockError("mock_approval_expired")
    approval["used"] = True


def _simulate_and_verify(manifest: dict[str, Any], contents: dict[str, bytes], variant: str) -> dict[str, Any]:
    target: dict[str, bytes] = {}
    for index, entry in enumerate(manifest["entries"]):
        if variant == "partial_copy" and index == len(manifest["entries"]) - 1:
            break
        if entry["target"] in target:
            raise ArchiveMockError("target_collision")
        data = contents[entry["id"]]
        target[entry["target"]] = data + b"corruption" if variant == "corrupt_target" and index == 0 else bytes(data)
    source_count = len(contents)
    source_bytes = sum(len(data) for data in contents.values())
    target_count = len(target)
    target_bytes = sum(len(data) for data in target.values())
    bad_ids = [entry["id"] for entry in manifest["entries"]
               if entry["target"] not in target or _sha(contents[entry["id"]]) != entry["sha256"]
               or _sha(target[entry["target"]]) != entry["sha256"]
               or len(target[entry["target"]]) != entry["size"]]
    verification = {"scope": "full_synthetic_in_memory", "expected_count": manifest["file_count"],
                    "source_count": source_count, "target_count": target_count,
                    "expected_bytes": manifest["source_bytes"], "source_bytes": source_bytes,
                    "target_bytes": target_bytes, "bad_ids": bad_ids, "source_preserved": True}
    if (bad_ids or source_count != manifest["file_count"] or target_count != manifest["file_count"]
            or source_bytes != manifest["source_bytes"] or target_bytes != manifest["source_bytes"]):
        raise ArchiveMockError("post_copy_integrity_failure", invalid_ids=bad_ids)
    verification["sha256_matches"] = True
    return verification


def run_archive_mock(runtime: MockRuntime, result: dict[str, Any], trace: list[str], *, variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"unknown photo_archive variant: {variant}")
    source = load_fixture("media", "bad_hash" if variant == "bad_hash" else "cases")
    files = source["files"]
    if variant == "missing_source":
        files[1].pop("content")
    elif variant == "unreadable_source":
        files[1]["readable"] = False
    elif variant == "path_escape":
        files[1]["path"] = "incoming/../outside/b.jpg"
    elif variant == "collision":
        files[1]["target_override"] = "archive/2024/A-A.JPG"  # collides after case normalization
    elif variant == "insufficient_capacity":
        source["destination_free_bytes"] = 1
    elif variant == "missing_backup":
        source["backup"]["verified"] = False
    runtime.event("friday-archive-inventory", "working", "Synthetic read-only scan started", 0)
    try:
        rows, contents = _inventory(source, trace)
        result["inventory"] = {"files": rows, "count": len(rows),
                               "bytes": sum(row["size"] for row in rows), "read_only": True}
        result["duplicate_groups"] = _groups(rows)
        trace.append("exact_duplicate_groups")
        manifest = _manifest(source, rows, runtime.now)
        result["manifest"] = manifest
        trace.append("reversible_copy_manifest")
        proposal = runtime.propose("archive_copy", manifest["target_root"], manifest,
                                   tier=risk_tier("archive_copy"))
        proposal["manifest_hash"] = action_fingerprint("archive_copy", manifest["target_root"], manifest)
        proposal["idempotency_key"] = f"synthetic-{proposal['manifest_hash'][:16]}"
        result["proposal"] = proposal
        result["approval"] = {"status": "required", "tier": 2, "granted": False,
                              "bound_manifest_hash": proposal["manifest_hash"],
                              "trusted_host_approval": False}
        result["status"] = "waiting_approval"
        trace.append("exact_manifest_approval_required")
        if variant in APPROVAL_VARIANTS:
            approval = _mock_approval(manifest, variant, runtime.now)
            _verify_mock_grant(approval, manifest, runtime.now)
            result["approval"] = {"status": "simulated_only", "tier": 2, "granted": True,
                                  "trusted_host_approval": False,
                                  "bound_manifest_hash": proposal["manifest_hash"]}
            trace.append("explicit_simulated_grant")
            result["verification"] = _simulate_and_verify(manifest, contents, variant)
            result["status"] = "completed"
            trace.extend(["in_memory_copy_only", "independent_full_sha256_count_bytes_check"])
    except (ArchiveMockError, KeyError, TypeError, ValueError) as exc:
        error = exc if isinstance(exc, ArchiveMockError) else ArchiveMockError("invalid_archive_fixture")
        result.update(status="blocked", reason=error.code)
        if error.invalid_ids:
            result["invalid_ids"] = error.invalid_ids
        if "manifest" not in result:
            result.pop("proposal", None)
        if "proposal" in result and variant in APPROVAL_VARIANTS:
            result["simulation_failed"] = True
    finally:
        runtime.event("friday-archive-inventory", result["status"],
                      "Synthetic archive flow " + result["status"],
                      1 if result["status"] == "completed" else 0.8 if result["status"] == "waiting_approval" else 0)
        result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
