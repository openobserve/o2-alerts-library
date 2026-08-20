#!/usr/bin/env python3
"""Validate every alert file in the library. Run on PRs, before the manifest.

`generate_manifest.py` already fails on the invariants it needs to build an
index (path depth, filename == name, severity, per-pack unique names). This
checks what a *consumer* needs and the generator does not look at: that the
file still deserializes into OpenObserve's `Alert`, that the gallery has a
title and a description to draw, and that a raw DB export has not been dropped
in with its instance fields intact.

Exit code 1 on any error; a clean run prints one summary line.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = ROOT / "packs"

SEVERITIES = ("critical", "warning", "info")

# PromQL keywords, matched case-insensitively because the language is
# (promql-parser lowercases before looking a keyword up).
SET_OPS = ("and", "or", "unless")
PROMQL_KEYWORDS = {
    "and", "or", "unless", "by", "without", "on", "ignoring", "group_left",
    "group_right", "offset", "bool", "sum", "avg", "min", "max", "count",
    "count_values", "group", "stddev", "stdvar", "topk", "bottomk", "quantile",
}
PLACEHOLDER = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")


def has_top_level_set_op(promql: str) -> str | None:
    """The name of an `and`/`or`/`unless` at paren depth 0, if there is one.

    OpenObserve runs `({promql}) {operator} {value}`, and `and`/`or`/`unless`
    bind LOOSER than a comparison. So a `promql` with one of them at the top
    level means the threshold was lifted out of a nested comparison and the
    parenthesised result parses differently from the rule it came from — the
    alert silently evaluates something else. A well-formed promql either has
    no set operator at all or has it inside parentheses.
    """
    i, n, depth = 0, len(promql), 0
    while i < n:
        c = promql[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c in "\"'`":
            quote, i = c, i + 1
            while i < n and promql[i] != quote:
                i += 2 if promql[i] == "\\" else 1
        elif depth == 0:
            m = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", promql[i:])
            if m:
                if m.group(0).lower() in SET_OPS:
                    return m.group(0)
                i += len(m.group(0))
                continue
        i += 1
    return None

# Fields that belong to one alert instance in one org's database, not to a
# library template: an installer must supply them per install. Rejecting them
# is what turns "someone pasted a DB export into a PR" from a silent
# customer-org failure into a build failure.
INSTANCE_FIELDS = (
    "id",
    "org_id",
    "destinations",
    "owner",
    "last_edited_by",
    "last_triggered_at",
    "last_satisfied_at",
    "updated_at",
)

# The two original packs predate the metadata backfill (library-repo-structure.md,
# migration step 3): they still carry instance fields and have no curated
# `title`/`severity`/`tags`. Everything else is held to the full contract from
# day one. This set shrinks to empty when the backfill lands — do not add to it.
BACKFILL_PENDING_PACKS = {"k8s", "openobserve"}

# OpenObserve's tag rules (config/src/meta/alerts/tags.rs): a tag must start
# with a letter, may contain letters, digits and `_-./:`, and is capped at 200
# characters, with at most 64 tags per alert. Library `tags` land in that field
# verbatim on install, so they have to satisfy it here.
TAG_CHARS_EXTRA = set("_-./:")
MAX_TAG_LEN = 200
MAX_TAGS = 64


def main() -> int:
    errors: list[str] = []
    checked = 0

    for path in sorted(PACKS_DIR.rglob("*.json")):
        rel = path.relative_to(ROOT).as_posix()
        parts = path.relative_to(PACKS_DIR).parts
        if len(parts) != 4 or parts[1] != "alerts":
            errors.append(f"{rel}: expected packs/<pack>/alerts/<category>/<name>.json")
            continue
        pack = parts[0]
        checked += 1

        def err(msg: str) -> None:
            errors.append(f"{rel}: {msg}")

        try:
            alert = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            err(f"invalid JSON: {e}")
            continue
        if not isinstance(alert, dict):
            err("top level must be a JSON object")
            continue

        if alert.get("name") != path.stem:
            err(f"filename '{path.stem}' != internal name '{alert.get('name')}'")
        description = (alert.get("description") or "").strip()
        if not description:
            err("empty description — the gallery card has nothing to show")
        # `description` is NOT row-templated: OpenObserve substitutes row
        # variables only into `row_template` and pastes the description in
        # flat, so a `{pod}` here renders as the literal text "{pod}" on the
        # gallery card and in every notification.
        stray = PLACEHOLDER.search(description)
        if stray:
            err(
                f"description contains {stray.group(0)!r}; row variables are only "
                "substituted into row_template, so this renders literally"
            )
        if alert.get("enabled") is not True:
            err("enabled must be true")
        if alert.get("is_real_time") is not False:
            err("is_real_time must be false — library alerts are scheduled")

        stream = alert.get("stream_name")
        if not stream or not isinstance(stream, str):
            err("stream_name is required")
        if alert.get("stream_type") not in ("logs", "metrics", "traces"):
            err(f"stream_type '{alert.get('stream_type')}' is not a stream type")

        qc = alert.get("query_condition") or {}
        qtype = qc.get("type")
        if qtype == "promql":
            promql = (qc.get("promql") or "").strip()
            if not promql:
                err("promql query is empty")
            # The mis-split check, for imported alerts only.
            #
            # OpenObserve runs `({promql}) {operator} {value}`, so a set
            # operator sitting at the top level of `promql` is FINE — the
            # wrapping parentheses put it back exactly where it was. What is
            # not fine is lifting a threshold out of an upstream expression
            # whose OUTERMOST operator is `and`/`or`/`unless`: those bind
            # looser than comparison, so the trailing comparison belonged to a
            # nested operand and the re-wrapped form parses differently from
            # the rule it came from. That is checked against the upstream
            # expression, which is the only place the original grouping
            # survives — and it is exactly the check that would have caught
            # `probe_http_status_code <= 199 OR probe_http_status_code >= 400`
            # being split into `(… <= 199 OR …) >= 400`.
            source = alert.get("source") or {}
            upstream = source.get("upstream_query")
            if upstream and "query_normalized" not in source:
                set_op = has_top_level_set_op(upstream)
                if set_op:
                    err(
                        f"the threshold was lifted out of an upstream expression "
                        f"whose outermost operator is '{set_op}' — the result "
                        "parses differently from the upstream rule; this query "
                        "must use the normalised form instead"
                    )
            if stream and stream.lower() in PROMQL_KEYWORDS:
                err(f"stream_name '{stream}' is a PromQL keyword, not a metric")
            cond = qc.get("promql_condition") or {}
            # OpenObserve runs `({promql}) {operator} {value}`; without the
            # condition the alert is rejected at save (AlertError::PromqlMissingQuery).
            if cond.get("operator") not in ("=", "!=", ">", ">=", "<", "<="):
                err(f"promql_condition.operator '{cond.get('operator')}' is invalid")
            if not isinstance(cond.get("value"), (int, float)):
                err("promql_condition.value must be a number")
        elif qtype == "sql":
            if not (qc.get("sql") or "").strip():
                err("sql query is empty")
        elif qtype != "custom":
            err(f"query_condition.type '{qtype}' is not one of promql/sql/custom")

        tc = alert.get("trigger_condition") or {}
        for field in ("period", "threshold", "frequency", "silence"):
            if not isinstance(tc.get(field), int) or tc[field] < 0:
                err(f"trigger_condition.{field} must be a non-negative integer")

        tags = alert.get("tags")
        if tags is not None:
            if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
                err("tags must be a list of strings")
            else:
                if len(tags) > MAX_TAGS:
                    err(f"{len(tags)} tags exceeds OpenObserve's cap of {MAX_TAGS}")
                for tag in tags:
                    if not tag[:1].isalpha():
                        err(f"tag '{tag}' must start with a letter")
                    elif not all(
                        c.isalnum() or c in TAG_CHARS_EXTRA for c in tag
                    ):
                        err(f"tag '{tag}' has a character OpenObserve rejects")
                    elif len(tag) > MAX_TAG_LEN:
                        err(f"tag '{tag}' is longer than {MAX_TAG_LEN} characters")

        if pack in BACKFILL_PENDING_PACKS:
            continue

        if alert.get("severity") not in SEVERITIES:
            err(f"severity must be one of {SEVERITIES}, got {alert.get('severity')!r}")
        if not (alert.get("title") or "").strip():
            err("title is required — the gallery card headline")
        present = [f for f in INSTANCE_FIELDS if f in alert]
        if present:
            err(
                f"instance-only field(s) {present} present — this looks like a raw "
                "export; library files carry the template, not one org's copy"
            )

    for e in errors:
        print(f"validate: ERROR: {e}", file=sys.stderr)
    if errors:
        print(f"validate: FAILED — {len(errors)} error(s) in {checked} files", file=sys.stderr)
        return 1
    print(f"validate: OK — {checked} alert files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
