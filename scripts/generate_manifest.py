#!/usr/bin/env python3
"""Generate manifest.json — the machine index of the alert library.

The UI reads ONLY this file to render the gallery (one GET, no S3 listing),
then fetches individual alert files at the `path` each entry states.

Rules this script enforces (it fails the build rather than emit a wrong index):
  - every alert lives at exactly packs/<pack>/alerts/<category>/<name>.json
  - filename == the alert's internal "name" field
  - alert names are unique per pack — "<pack>/<name>" is the stable `id`
    installers stamp for provenance/update detection, so a collision is a
    build error, not a surprise in a customer org
  - severity comes from an explicit "severity" field, or deterministically
    from the description's "Critical:/Warning:/Info:" prefix — an alert with
    neither is an error, never a silent default

Each entry also carries `content_hash` (sha256 of the alert file, first 12
hex chars) for mechanical update detection.

Determinism is load-bearing: same tree in, byte-identical manifest out
(sorted traversal, no timestamps). CI relies on "no diff => no bot commit"
to avoid retrigger loops. Do not add anything time- or environment-dependent.

In-file fields (title, tags, tier, version, docs_url) win over derived values,
so the metadata backfill enriches the manifest without touching this script.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

FORMAT_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = ROOT / "packs"
OUT = ROOT / "manifest.json"

SEVERITIES = ("critical", "warning", "info")
SEV_PREFIX = re.compile(r"^\s*(critical|warning|info)\b", re.IGNORECASE)


def fail(msg: str) -> None:
    print(f"manifest: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def derive_title(name: str) -> str:
    # Mechanical fallback until the metadata backfill adds curated titles
    # (this yields "Pod Oom Killed"; the backfill will fix acronym casing).
    return " ".join(w.capitalize() for w in name.split("_"))


def derive_severity(alert: dict, rel: str) -> str:
    if "severity" in alert:
        sev = alert["severity"]
        if sev not in SEVERITIES:
            fail(f"{rel}: severity '{sev}' not one of {SEVERITIES}")
        return sev
    m = SEV_PREFIX.match(alert.get("description") or "")
    if not m:
        fail(
            f"{rel}: no 'severity' field and description lacks a "
            "'Critical:'/'Warning:'/'Info:' prefix — declare severity explicitly"
        )
    return m.group(1).lower()


def main() -> None:
    if not PACKS_DIR.is_dir():
        fail("packs/ directory not found (run from the repo, layout per design notes)")

    packs = []
    alerts = []

    for pack_dir in sorted(p for p in PACKS_DIR.iterdir() if p.is_dir()):
        pack = pack_dir.name
        alerts_dir = pack_dir / "alerts"
        if not alerts_dir.is_dir():
            fail(f"packs/{pack}/ has no alerts/ directory")

        stray = sorted(alerts_dir.glob("*.json"))
        if stray:
            fail(
                f"{stray[0].relative_to(ROOT)}: alert JSON must live in a "
                f"category folder (packs/{pack}/alerts/<category>/), not directly "
                f"under alerts/"
            )

        # `id` (<pack>/<name>) is the stable key installers stamp into customer
        # orgs (provenance / update detection), so collisions must be build
        # errors: the filesystem only prevents same-name within one category.
        seen_names: dict[str, str] = {}

        categories = []
        for cat_dir in sorted(p for p in alerts_dir.iterdir() if p.is_dir()):
            category = cat_dir.name
            nested = [p for p in cat_dir.rglob("*.json") if p.parent != cat_dir]
            if nested:
                fail(f"{nested[0].relative_to(ROOT)}: nested deeper than a category folder")
            files = sorted(cat_dir.glob("*.json"))
            if not files:
                fail(f"packs/{pack}/alerts/{category}/ is empty — delete the folder or add alerts")

            categories.append({"id": category, "alert_count": len(files)})

            for f in files:
                rel = f.relative_to(ROOT).as_posix()
                raw = f.read_bytes()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as e:
                    fail(f"{rel}: invalid JSON: {e}")
                if data.get("name") != f.stem:
                    fail(f"{rel}: filename '{f.stem}' != internal name '{data.get('name')}'")
                if data["name"] in seen_names:
                    fail(
                        f"{rel}: duplicate alert name '{data['name']}' in pack "
                        f"'{pack}' (also at {seen_names[data['name']]}) — names "
                        "must be unique per pack; they form the stable id"
                    )
                seen_names[data["name"]] = rel

                qc = data.get("query_condition") or {}
                entry = {
                    "id": f"{pack}/{data['name']}",
                    "name": data["name"],
                    "pack": pack,
                    "category": category,
                    "title": data.get("title") or derive_title(data["name"]),
                    "severity": derive_severity(data, rel),
                    "description": (data.get("description") or "").strip(),
                    "stream": data.get("stream_name"),
                    "stream_type": data.get("stream_type"),
                    "query_type": qc.get("type"),
                    "required_streams": [data["stream_name"]] if data.get("stream_name") else [],
                    "path": rel,
                    # Mechanical change detection: installers stamp this hash;
                    # the gallery compares stamp vs manifest to show "update
                    # available". Nobody has to remember to bump anything. A
                    # curated semver `version` field can layer on top later.
                    "content_hash": hashlib.sha256(raw).hexdigest()[:12],
                }
                for optional in ("tags", "tier", "version", "docs_url"):
                    if optional in data:
                        entry[optional] = data[optional]
                alerts.append(entry)

        packs.append(
            {
                "id": pack,
                "categories": categories,
                "alert_count": sum(c["alert_count"] for c in categories),
            }
        )

    manifest = {
        "format_version": FORMAT_VERSION,
        "alert_count": len(alerts),
        "packs": packs,
        "alerts": alerts,
    }
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"manifest: OK — {len(alerts)} alerts, {len(packs)} packs -> {OUT.name}")


if __name__ == "__main__":
    main()
