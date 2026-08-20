#!/usr/bin/env python3
"""Import the awesome-prometheus-alerts rule set into this library.

Source: https://github.com/samber/awesome-prometheus-alerts (`_data/rules.yml`),
rules and content licensed CC BY 4.0 — see ATTRIBUTION.md.

Run:
    python3 scripts/import_awesome_prometheus_alerts.py \
        --source ../awesome-prometheus-alerts/_data/rules.yml

The script is idempotent: same rules.yml in, byte-identical tree out. It only
writes under the packs it owns (PACKS_OWNED), wiping them first, so a re-run
after an upstream refresh also removes rules upstream deleted. It never touches
`packs/k8s` or `packs/openobserve`.

## How a Prometheus rule becomes an OpenObserve alert

OpenObserve evaluates a PromQL alert by running `({promql}) {op} {value}`
(src/core/src/alerts/mod.rs) — so the threshold must live in
`query_condition.promql_condition`, NOT baked into the expression. Upstream
rules bake it in, so every query is split:

  * `node_load1 > 5`      -> promql `node_load1`, condition `> 5`
  * `up == 0 unless ...`  -> cannot split (the outermost operator is `unless`,
    which binds looser than `==`, so pulling the comparison out would change
    the parse). These fall back to `(<query>) * 0 + 1` with condition `>= 1`:
    every series the upstream rule would have matched gets value 1 and fires,
    labels preserved. The observed value is then a constant, which is why the
    upstream expression is also kept verbatim in `source.upstream_query`.

`for: 5m` becomes `trigger_condition.period` (minutes, clamped to 1..60): the
closest available notion of "the condition held over this window".
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = ROOT / "packs"

UPSTREAM = "awesome-prometheus-alerts"
UPSTREAM_LICENSE = "CC-BY-4.0"
UPSTREAM_SITE = "https://samber.github.io/awesome-prometheus-alerts"

# Upstream group -> pack in this library. Slugs are ours: shorter and closer to
# how the gallery reads. Upstream "Other" is dissolved (see SERVICE_PACK).
GROUP_PACK = {
    "Basic resource monitoring": "infrastructure",
    "Databases": "databases",
    "Message brokers": "message-brokers",
    "Proxies, load balancers and service meshes": "proxies-and-service-mesh",
    "Runtimes": "runtimes",
    "Data engineering": "data-engineering",
    "Orchestrators": "orchestrators",
    "CI/CD": "ci-cd",
    "Network and security": "network-and-security",
    "Storage": "storage",
    "Cloud providers": "cloud-providers",
    "Observability": "observability",
}

# Per-service overrides. Upstream's catch-all "Other" group is not a useful
# gallery pack, so its three services are placed by what they actually are.
SERVICE_PACK = {
    "APC UPS": "infrastructure",
    # Monitoring the monitoring belongs with the rest of the observability
    # stack, not with hosts and hardware.
    "Prometheus self-monitoring": "observability",
    "Graph Node": "applications",
    "LiteLLM": "applications",
}

# The packs this importer owns end to end. Anything here is deleted and
# rewritten on every run; nothing outside is touched.
PACKS_OWNED = sorted(set(GROUP_PACK.values()) | set(SERVICE_PACK.values()))

# Hand-authored packs. The mappings above are edited by humans, and a typo that
# pointed one at "k8s" would silently delete 86 curated alerts on the next run.
PACKS_NEVER_TOUCHED = {"k8s", "openobserve"}
assert not (set(PACKS_OWNED) & PACKS_NEVER_TOUCHED), (
    "a pack mapping targets a hand-authored pack, which this script deletes: "
    f"{sorted(set(PACKS_OWNED) & PACKS_NEVER_TOUCHED)}"
)

# Display name + one-line blurb per pack, for the generated pack README.
PACK_INFO = {
    "applications": (
        "Applications",
        "Application-level services that expose their own Prometheus metrics.",
    ),
    "ci-cd": ("CI/CD", "Build, delivery and GitOps pipelines."),
    "cloud-providers": (
        "Cloud providers",
        "Cloud platform resources scraped through provider exporters.",
    ),
    "data-engineering": (
        "Data engineering",
        "Batch and stream processing clusters.",
    ),
    "databases": (
        "Databases",
        "Relational, document, key-value and search datastores.",
    ),
    "infrastructure": (
        "Infrastructure",
        "Hosts, hardware, containers and the agents that watch them.",
    ),
    "message-brokers": (
        "Message brokers",
        "Queues, streams and their consumers.",
    ),
    "network-and-security": (
        "Network and security",
        "DNS, certificates, VPNs, secret stores and identity providers.",
    ),
    "observability": (
        "Observability",
        "The monitoring stack itself — Prometheus, Thanos, Loki, Tempo, Mimir "
        "and friends.",
    ),
    "orchestrators": (
        "Orchestrators",
        "Cluster schedulers and the control planes behind them.",
    ),
    "proxies-and-service-mesh": (
        "Proxies and service mesh",
        "Reverse proxies, load balancers and mesh data planes.",
    ),
    "runtimes": (
        "Runtimes",
        "Language runtimes and their process managers.",
    ),
    "storage": ("Storage", "Object stores, block storage and clustered filesystems."),
}

# Category slug overrides where mechanical slugification reads badly.
SERVICE_CATEGORY = {
    "S.M.A.R.T Device Monitoring": "smart-device-monitoring",
    "SSL/TLS": "ssl-tls",
    "Prometheus self-monitoring": "prometheus",
    "Host and hardware": "host-and-hardware",
    "Google Cloud Stackdriver": "google-cloud-stackdriver",
    "AWS CloudWatch": "aws-cloudwatch",
}

SEVERITIES = ("critical", "warning", "info")

SYNTHETIC_QUERY_STREAM = "up"

# A query that selects nothing at all — the Alertmanager dead-man's switch is
# literally `vector(1)`. It reads no stream, but the field is mandatory.
SYNTHETIC_QUERY = re.compile(r"^\s*vector\s*\(")

# `stream_name` must name a real stream: OpenObserve looks up its schema at save
# time and refuses the alert with `StreamNotFound` if it has never been ingested
# (`src/core/src/alerts/alert.rs`). A query that selects a whole FAMILY of
# metrics by regex has no single stream, so those are named here explicitly
# rather than guessed. Keyed by alert name; unresolvable-and-unlisted is a build
# error, never a truncated prefix.
METRIC_OVERRIDES = {
    # `{__name__=~"pg_settings_.*"} != ON(...) ... OFFSET 5m` compares every
    # pg_settings_* gauge with its value 5m ago. Any one of them is a correct
    # stream association; max_connections is present in every postgres_exporter
    # deployment.
    "postgresql_configuration_changed": "pg_settings_max_connections",
    # Counts series across EVERY metric (`{__name__=~".+"}`), so no one stream
    # is "the" stream. `up` exists wherever Prometheus metrics are ingested.
    "prometheus_timeseries_cardinality": SYNTHETIC_QUERY_STREAM,
}

# Upstream queries that do not parse as PromQL, fixed on the way in. Keys are
# the exact upstream expression; a key that stops matching is a build error, so
# a fixup cannot silently outlive the bug it patches.
QUERY_FIXUPS = {
    # `\.` is not a legal escape inside a PromQL double-quoted string (Go
    # escape rules), so upstream's expression is rejected by the parser.
    # Doubling the backslashes yields the intended `\.` in the regex.
    'count(count by (git_version) (label_replace(kubernetes_build_info, "git_version", "$1", "git_version", "(v[0-9]*\\.[0-9]*\\.[0-9]*).*"))) > 1':
        'count(count by (git_version) (label_replace(kubernetes_build_info, "git_version", "$1", "git_version", "(v[0-9]*\\\\.[0-9]*\\\\.[0-9]*).*"))) > 1',
}

# Alerts are evaluated no more often than this and no less often than 1/min.
FREQ_FAST_MINUTES = 1
FREQ_SLOW_MINUTES = 5
PERIOD_MIN, PERIOD_MAX = 1, 60
SILENCE_MINUTES = 60

# Floor on a successful import. Upstream ships ~1,155 rules; anything an order
# of magnitude below that means the source file is not what we think it is, and
# the wipe-then-write below must not proceed. Deliberately well under the real
# count so ordinary upstream churn does not trip it.
MIN_EXPECTED_ALERTS = 900


def fail(msg: str) -> None:
    print(f"import: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def to_slug(name: str) -> str:
    """Mirrors upstream's site slugifier (lowercase, non-alnum -> '-')."""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", name.lower()))


def to_name(text: str) -> str:
    """Alert `name` == filename: lowercase, non-alnum -> '_'."""
    return re.sub(r"^_+|_+$", "", re.sub(r"[^a-z0-9]+", "_", text.lower()))


# --------------------------------------------------------------------------
# PromQL: split the baked-in threshold out of the expression
# --------------------------------------------------------------------------

# PromQL keywords are CASE-INSENSITIVE (the parser lowercases before matching:
# promql-parser `lex.rs`, `get_keyword_token(&s.to_lowercase())`), and upstream
# really does write `OR`/`AND`/`OFFSET`/`BY`. Matching these case-sensitively
# silently defeated the outermost-operator guard below and mis-split two rules,
# so every keyword test in this file lowercases first.
SET_OPS = ("and", "or", "unless")
NUM_EXPR = re.compile(r"^[\s0-9eE.+\-*/()]+$")
# JSON operator vocabulary is OpenObserve's `Operator` enum: equality is "=".
OP_JSON = {"==": "=", "!=": "!=", ">=": ">=", "<=": "<=", ">": ">", "<": "<"}


def strip_outer_parens(q: str) -> str:
    """Drop parens that wrap the whole expression, e.g. `(a > 1)` -> `a > 1`."""
    q = q.strip()
    while q.startswith("(") and q.endswith(")"):
        depth = 0
        for i, c in enumerate(q):
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0 and i != len(q) - 1:
                    return q  # the leading "(" closes early: not a wrapper
        q = q[1:-1].strip()
    return q


def top_level_tokens(q: str):
    """(kind, text, offset) for comparison ops and set ops at paren depth 0."""
    toks, i, n, depth = [], 0, len(q), 0
    while i < n:
        c = q[i]
        if c in "([{":
            depth += 1
            i += 1
            continue
        if c in ")]}":
            depth -= 1
            i += 1
            continue
        if c in "\"'`":
            quote, i = c, i + 1
            while i < n and q[i] != quote:
                i += 2 if q[i] == "\\" else 1
            i += 1
            continue
        if depth == 0:
            if q[i : i + 2] in ("==", "!=", ">=", "<="):
                toks.append(("cmp", q[i : i + 2], i))
                i += 2
                continue
            if c in "<>":
                toks.append(("cmp", c, i))
                i += 1
                continue
            m = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", q[i:])
            if m:
                if m.group(0).lower() in SET_OPS:
                    toks.append(("setop", m.group(0), i))
                i += len(m.group(0))
                continue
        i += 1
    return toks


def split_threshold(query: str):
    """-> (expr, json_operator, value) or None when the query cannot be split.

    Safe only when the comparison is the outermost operator. `and`/`or`/`unless`
    bind looser than comparison, so any of them at depth 0 means the trailing
    comparison is nested and must not be pulled out.
    """
    q = strip_outer_parens(query)
    toks = top_level_tokens(q)
    if not toks or any(t[0] == "setop" for t in toks):
        return None
    kind, op, pos = toks[-1]
    if kind != "cmp":
        return None
    lhs, rhs = q[:pos].strip(), q[pos + len(op) :].strip()
    if not lhs or rhs.startswith("bool") or not NUM_EXPR.match(rhs):
        return None
    try:
        value = eval(rhs, {"__builtins__": {}}, {})  # noqa: S307 — digits/±*/() only
    except Exception:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return strip_outer_parens(lhs), OP_JSON[op], value


def to_promql_alert(query: str):
    """-> (promql, promql_condition_operator, value, was_normalized)."""
    split = split_threshold(query)
    if split:
        expr, op, value = split
        return expr, op, value, False
    # Fallback: force every matching series to 1 so a plain `>= 1` fires
    # exactly when the upstream rule would, with labels intact.
    return f"({query.strip()}) * 0 + 1", ">=", 1, True


# --------------------------------------------------------------------------
# PromQL: which metric (= OpenObserve stream) does this alert read?
# --------------------------------------------------------------------------

PROMQL_KEYWORDS = {
    "and", "or", "unless", "by", "without", "on", "ignoring", "group_left",
    "group_right", "offset", "bool", "start", "end", "inf", "nan", "atan2",
}

# Aggregation operators are the trap here: unlike functions they are NOT
# followed by "(" when a modifier comes first — `sum by (job) (up)` — so the
# "identifier not followed by (" test would happily return `sum` as the metric.
PROMQL_AGGREGATIONS = {
    "sum", "avg", "min", "max", "count", "count_values", "group", "stddev",
    "stdvar", "topk", "bottomk", "quantile", "limitk", "limit_ratio",
}

# ... and the modifier's own parentheses hold LABEL names, not metrics, so
# `by (instance)` must be removed before the scan rather than skipped during it.
GROUPING_CLAUSE = re.compile(
    r"\b(?:by|without|on|ignoring|group_left|group_right)\s*\([^()]*\)",
    re.IGNORECASE,
)


def primary_metric(query: str) -> str | None:
    """First metric selector in the query — the stream the alert reads."""
    # Drop label matchers, range/offset brackets, string literals and grouping
    # clauses, so none of their identifiers (`job`, `fstype`, `5m`, `instance`)
    # can be mistaken for a metric name.
    stripped = re.sub(r"\{[^{}]*\}", " ", query)
    stripped = re.sub(r"\[[^\[\]]*\]", " ", stripped)
    stripped = re.sub(r'"[^"]*"', " ", stripped)
    stripped = GROUPING_CLAUSE.sub(" ", stripped)
    for m in re.finditer(r"[a-zA-Z_:][a-zA-Z0-9_:]*", stripped):
        word = m.group(0)
        if word.lower() in PROMQL_KEYWORDS or word.lower() in PROMQL_AGGREGATIONS:
            continue
        if stripped[m.end() : m.end() + 1] == "(":  # a function call
            continue
        return word
    # No bare selector: the query matches by `__name__` alone. Resolve the
    # regex to ONE concrete metric by taking the first branch of each
    # alternation — `otelcol_receiver_refused_(spans|log_records)_total`
    # really is `otelcol_receiver_refused_spans_total`, a metric that exists.
    # A bare-prefix wildcard (`pg_settings_.*`) names no single metric, so it
    # resolves to nothing here and must come from METRIC_OVERRIDES; returning
    # the truncated prefix would put a non-existent stream in the manifest.
    m = re.search(r'__name__\s*=~?\s*"([^"]+)"', query)
    if m:
        expanded = re.sub(r"\(([^()|]+)(?:\|[^()]*)?\)", r"\1", m.group(1))
        if re.fullmatch(r"[a-zA-Z_:][a-zA-Z0-9_:]*", expanded):
            return expanded
    return None


# --------------------------------------------------------------------------
# Go/Prometheus annotation templating -> OpenObserve variables
# --------------------------------------------------------------------------

# Upstream descriptions are Prometheus annotations, so they carry Go template
# actions: `{{ $labels.instance }}`, `{{ $value | humanize }}`,
# `{{ printf "%.2f" $value }}`. OpenObserve substitutes `{name}` instead, and a
# PromQL alert row is exactly the series labels plus `value`
# (src/core/src/alerts/mod.rs) — so every one of these actions has a direct
# OpenObserve equivalent and the text is rewritten rather than stripped.
TPL_VALUE = re.compile(r"\{\{[^{}]*\$value[^{}]*\}\}")
TPL_LABEL = re.compile(r"\{\{\s*\$labels\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
TPL_ANY = re.compile(r"\{\{.*?\}\}")

PLACEHOLDER = r"\{[a-zA-Z_][a-zA-Z0-9_]*\}"
# `{value}` together with any unit glued to it — "{value}s", "{value}ms",
# "{value}%". Without this the unit is left stranded ("latency of {value}s"
# would clean to "latencys").
VALUE_TOKEN = r"\{value\}(?:%|[a-zA-Z]{1,2}\b)?"


def rewrite_template(text: str) -> str:
    """Go template actions -> OpenObserve row variables."""
    text = TPL_VALUE.sub("{value}", text)
    return TPL_LABEL.sub(lambda m: "{" + m.group(1) + "}", text)


# ---------------------------------------------------------------------------
# The description is NOT a row template
# ---------------------------------------------------------------------------
#
# This is the trap: OpenObserve substitutes row variables ONLY into
# `row_template` (`process_row_template`, src/core/src/alerts/alert.rs). The
# description is copied flat into the notification context as
# `alert_description` and pasted in with a plain string replace — so a `{pod}`
# left in it renders as the literal text "{pod}", both in the gallery card and
# in every notification.
#
# Upstream descriptions are firing MESSAGES ("Pod {pod} is crash looping").
# A library card needs a STATEMENT of what the alert detects ("Pod is crash
# looping"). These rules do that conversion: they delete the interpolations and
# repair the grammar around the hole. Verified across all 1,155 upstream
# descriptions — zero placeholders survive, zero descriptions are emptied.
DESC_RULES = [
    # "(instance {instance})", "({value} in the last 5m)", "({value}%)"
    (re.compile(r"\s*\([^()]*" + PLACEHOLDER + r"[^()]*\)"), ""),
    # "{value}%" first: it is a QUANTITY, and the verb rules below would
    # otherwise eat it and leave the preposition stranded ("using of X").
    (re.compile(r"\{value\}\s*%"), "a high percentage"),
    # trailing "- {cluster}"
    (re.compile(r"\s*[-\u2013\u2014]\s*" + PLACEHOLDER
                + r"(\s*/\s*" + PLACEHOLDER + r")*\s*(?=[.!?]?$)"), ""),
    # "is {value}", "has {value}" -> keep the verb, drop the number
    (re.compile(r"\b(?:is|are|has|have|was|were)\s+" + VALUE_TOKEN),
     lambda m: m.group(0).split()[0]),
    (re.compile(r"\b(?:reached|encountered|returning|using|reporting|refusing)\s+"
                + VALUE_TOKEN), lambda m: m.group(0).split()[0]),
    # "on {instance}", "in {namespace}/{pod}", "for {job}", "of {value}s"
    (re.compile(r"\s+\b(?:on|in|for|of|from|at|to|under|by)\s+(?:" + VALUE_TOKEN
                + r"|" + PLACEHOLDER + r"(\s*/\s*" + PLACEHOLDER + r")*)"), ""),
    (re.compile(r"\s*" + VALUE_TOKEN + r"\s*"), " "),
    # "sensor {name} is" -> "sensor is": the noun already carries the meaning
    (re.compile(r"(\w)\s+" + PLACEHOLDER + r"(\s*/\s*" + PLACEHOLDER + r")*"), r"\1"),
    (re.compile(r"\s*" + PLACEHOLDER + r"(\s*/\s*" + PLACEHOLDER + r")*\s*"), " "),
]
DESC_TIDY = [
    (re.compile(r"\s{2,}"), " "),
    (re.compile(r"\s+([.,;:!?%])"), r"\1"),
    (re.compile(r"\s*,\s*(?=[.!?]|$)"), ""),
    (re.compile(r"\b(of|to|for|in|on|at|by)\s+(of|to|for|in|on|at|by)\b"), r"\1"),
    (re.compile(r"\s*:\s*(?=[.!?]|$)"), ""),
    # last resort: a verb left dangling in front of a preposition
    (re.compile(r"\b(is|are|has|have|was|were|using|returning|reporting|refusing)"
                r"\s+(?:of|to|for|by|at)\s+"), r"\1 "),
]


def card_description(templated: str) -> str:
    """Upstream's firing message -> a placeholder-free catalogue description."""
    text = templated
    for rx, rep in DESC_RULES:
        text = rx.sub(rep, text)
    for rx, rep in DESC_TIDY:
        text = rx.sub(rep, text)
    text = text.strip()
    return text[0].upper() + text[1:] if text else text


def described_labels(text: str) -> list[str]:
    """Series labels the upstream annotation names, in order, de-duplicated.

    A label the annotation interpolates is normally a label the firing series
    carries, since the annotation is rendered against this very expression's
    output — but "normally" is not "always" (see `output_labels`).
    """
    out: list[str] = []
    for m in TPL_LABEL.finditer(text):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out


# ---------------------------------------------------------------------------
# Which labels can the result actually carry?
# ---------------------------------------------------------------------------

# Functions that pass their input's labels straight through, so the label set
# is decided by the expression nested inside them.
LABEL_TRANSPARENT = {
    "rate", "irate", "increase", "delta", "idelta", "deriv", "abs", "round",
    "floor", "ceil", "clamp_max", "clamp_min", "sqrt", "ln", "log2", "log10",
    "avg_over_time", "min_over_time", "max_over_time", "sum_over_time",
    "last_over_time", "stddev_over_time", "quantile_over_time", "predict_linear",
    "histogram_quantile",
}
# `sum by (job) (x)` and `sum(x) by (job)` are both legal PromQL and upstream
# uses both, so the modifier is matched on either side of the argument list.
AGG_NAMES = "|".join(sorted(PROMQL_AGGREGATIONS))
ROOT_AGG_LEADING = re.compile(
    r"^\s*(?:" + AGG_NAMES + r")\s*(?:(by|without)\s*\(([^()]*)\))?\s*\(", re.IGNORECASE
)
TRAILING_MODIFIER = re.compile(r"\)\s*(by|without)\s*\(([^()]*)\)\s*$", re.IGNORECASE)
ROOT_FUNCTION = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.IGNORECASE)
# Vector matching can ADD labels (group_left copies them across), so any of
# these at the top level means the label set is not ours to predict.
VECTOR_MATCHING = re.compile(
    r"(?<![a-zA-Z0-9_])(on|ignoring|group_left|group_right)\s*\(", re.IGNORECASE
)
BINARY_OPS = re.compile(r"[+\-*/%^]")


def _spans_whole_expression(text: str, open_at: int) -> bool:
    """Does the '(' at `open_at` close only at the very end of `text`?"""
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1 :].strip() == ""
    return False


def _split_top_level_operands(text: str) -> list[str]:
    """Operands of the top-level binary operators, in order."""
    parts, depth, start, i, n = [], 0, 0, 0, len(text)
    while i < n:
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c in "\"'`":
            quote, i = c, i + 1
            while i < n and text[i] != quote:
                i += 2 if text[i] == "\\" else 1
        elif depth == 0:
            if text[i : i + 2] in ("==", "!=", ">=", "<="):
                parts.append(text[start:i]); i += 2; start = i; continue
            word = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", text[i:])
            if word and word.group(0).lower() in SET_OPS:
                parts.append(text[start:i]); i += len(word.group(0)); start = i; continue
            if word:
                i += len(word.group(0)); continue
            if c in "<>" or BINARY_OPS.fullmatch(c):
                parts.append(text[start:i]); i += 1; start = i; continue
        i += 1
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


def output_labels(query: str, depth: int = 0) -> set[str] | None:
    """Labels the expression's result carries, or None when not determinable.

    Only decides what can be decided: an aggregation at the root fixes the set
    exactly (`sum by (job) (…)` yields `job` and nothing else, a bare `sum(…)`
    yields none). For a binary expression it follows the LEFT operand, which is
    exact for `and`/`unless` and an upper bound elsewhere. Anything involving
    explicit vector matching, or anything it cannot recognise, returns None —
    and callers must read None as "do not filter", because guessing wrong here
    strips real context out of a correct notification.
    """
    if depth > 6:
        return None
    q = strip_outer_parens(query)

    if VECTOR_MATCHING.search(q):
        toks = _split_top_level_operands(q)
        if len(toks) > 1:
            return None

    operands = _split_top_level_operands(q)
    if len(operands) > 1:
        for operand in operands:
            if re.fullmatch(r"[\s0-9eE.+\-]*", operand):
                continue  # a bare number contributes no labels
            return output_labels(operand, depth + 1)
        return None

    trailing = TRAILING_MODIFIER.search(q)
    if trailing and ROOT_AGG_LEADING.match(q):
        if trailing.group(1).lower() == "without":
            return None
        return {lbl.strip() for lbl in trailing.group(2).split(",") if lbl.strip()}

    agg = ROOT_AGG_LEADING.match(q)
    if agg and _spans_whole_expression(q, q.index("(", agg.end() - 1)):
        if agg.group(1) and agg.group(1).lower() == "by":
            return {lbl.strip() for lbl in agg.group(2).split(",") if lbl.strip()}
        if agg.group(1):  # `without (...)` keeps every OTHER label
            return None
        return set()  # bare aggregation collapses everything

    fn = ROOT_FUNCTION.match(q)
    if fn and fn.group(1).lower() in LABEL_TRANSPARENT and q.endswith(")"):
        inner = q[fn.end() : q.rindex(")")]
        args, d, start = [], 0, 0
        for i, c in enumerate(inner):
            if c in "([{":
                d += 1
            elif c in ")]}":
                d -= 1
            elif c == "," and d == 0:
                args.append(inner[start:i]); start = i + 1
        args.append(inner[start:])
        return output_labels(args[-1], depth + 1)  # the vector is the last arg
    return None


def row_template(labels: list[str], *, show_value: bool) -> str:
    """Per-series line: the labels this alert can actually report, plus value.

    `show_value` is false for normalised queries, where the expression pins
    every series to 1 — printing "value: 1" would state a fact that is an
    artefact of the conversion, not an observation.
    """
    parts = [f"{label}: {{{label}}}" for label in labels]
    if show_value:
        parts.append("value: {value}")
    if not parts:
        return "*{alert_name}*"
    return "*{alert_name}* | " + " | ".join(parts)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build_alert(
    rule, *, name, category, service, exporter, group, promql_bits, upstream_query
):
    promql, op, value, normalized = promql_bits
    # A synthetic query (`vector(1)`, the dead-man's switch) selects no metric
    # at all, but `stream_name` is required. `up` is the safe stand-in: it
    # exists wherever Prometheus metrics are ingested, and the field only
    # associates the alert with a stream — the query does not read it.
    metric = METRIC_OVERRIDES.get(name) or primary_metric(rule["query"])
    if not metric:
        if SYNTHETIC_QUERY.search(rule["query"]):
            metric = SYNTHETIC_QUERY_STREAM
        else:
            fail(
                f"{name}: cannot resolve a stream from the query — add an entry "
                f"to METRIC_OVERRIDES: {rule['query']}"
            )
    if metric.lower() in PROMQL_KEYWORDS or metric.lower() in PROMQL_AGGREGATIONS:
        fail(f"{name}: resolved stream '{metric}' is a PromQL keyword, not a metric")

    for_minutes = parse_duration_minutes(rule.get("for"))
    period = max(PERIOD_MIN, min(PERIOD_MAX, for_minutes))
    frequency = FREQ_FAST_MINUTES if period <= 5 else FREQ_SLOW_MINUTES

    raw_description = " ".join((rule.get("description") or "").split())
    templated = rewrite_template(raw_description)
    description = card_description(templated)

    # Only report labels the result provably carries. Upstream annotations
    # sometimes name a label their own expression aggregates away — a real
    # upstream bug, which would render here as a literal "instance: {instance}"
    # in every notification row.
    labels = described_labels(raw_description)
    carried = output_labels(rule["query"] if normalized else promql)
    dropped = [] if carried is None else [x for x in labels if x not in carried]
    if dropped:
        labels = [x for x in labels if x not in dropped]

    severity = (rule.get("severity") or "").lower()
    if severity not in SEVERITIES:
        fail(f"{name}: severity '{rule.get('severity')}' not one of {SEVERITIES}")

    source = {
        "project": UPSTREAM,
        "license": UPSTREAM_LICENSE,
        "url": f"{UPSTREAM_SITE}/rules/{to_slug(group)}/{to_slug(service)}/",
        "exporter": exporter,
        "upstream_alert": rule["name"],
        "upstream_query": upstream_query,
        "upstream_description": raw_description,
    }
    if dropped:
        source["labels_dropped"] = (
            "The upstream annotation interpolates " + ", ".join(sorted(dropped))
            + ", but this expression aggregates those labels away, so they are "
            "not in row_template — they would render as literal placeholders."
        )
    if for_minutes > period:
        source["period_clamped_from"] = (
            f"Upstream `for` is {rule.get('for')} ({for_minutes} minutes); the "
            f"evaluation window is capped at {PERIOD_MAX} minutes. Widen "
            "trigger_condition.period if you want the full upstream window."
        )
    if rule["query"].strip() != upstream_query:
        source["query_fixup"] = (
            "The upstream expression above does not parse as PromQL; the "
            "corrected form this alert runs is in `query_condition.promql`. "
            "See QUERY_FIXUPS in scripts/import_awesome_prometheus_alerts.py."
        )
    if normalized:
        source["query_normalized"] = (
            "The upstream threshold could not be lifted out of the expression "
            "(its outermost operator is and/or/unless, or it compares against "
            "another series), so the expression is normalised to 1 per matching "
            "series and the alert fires on any match. The observed value in the "
            "notification is therefore always 1."
        )

    alert = {
        "name": name,
        "title": rule["name"].strip(),
        "severity": severity,
        "description": description,
        "tags": sorted({UPSTREAM, category, exporter}),
        "docs_url": source["url"],
        "source": source,
        "stream_type": "metrics",
        "stream_name": metric,
        "is_real_time": False,
        "query_condition": {
            "type": "promql",
            "conditions": {
                "version": 2,
                "conditions": {
                    "filterType": "group",
                    "logicalOperator": "AND",
                    "conditions": [],
                },
            },
            "sql": None,
            "promql": promql,
            "promql_condition": {
                "column": "value",
                "operator": op,
                "value": value,
                "ignore_case": False,
            },
            "aggregation": None,
            "vrl_function": None,
            "search_event_type": None,
            "multi_time_range": [],
        },
        "trigger_condition": {
            "period": period,
            "operator": ">=",
            "threshold": 1,
            "frequency": frequency,
            "cron": "",
            "frequency_type": "minutes",
            "silence": SILENCE_MINUTES,
            "timezone": "UTC",
            "tolerance_in_secs": None,
            "align_time": True,
        },
        "context_attributes": {},
        # Built only from labels the upstream annotation itself interpolates
        # (see `described_labels`), plus `value`, which every PromQL alert row
        # carries. Guessing at `{instance}`/`{pod}` across 1000+ unrelated
        # queries would render a literal placeholder wherever the series has
        # no such label.
        "row_template": row_template(labels, show_value=not normalized),
        "row_template_type": "String",
        "enabled": True,
        "tz_offset": 0,
        "creates_incident": False,
    }
    notes = rewrite_template((rule.get("comments") or "").strip())
    if notes:
        alert["notes"] = notes

    # Checked on the fields that RENDER, not on `source` — which deliberately
    # preserves upstream's description verbatim, Go template actions and all,
    # exactly as it preserves the upstream query.
    rendered = [alert["title"], alert["description"], alert["row_template"],
                alert.get("notes", "")]
    leftover = TPL_ANY.search(" ".join(rendered))
    if leftover:
        fail(f"{name}: unconverted Go template action {leftover.group(0)!r}")
    # The card and the notification body both render `description` verbatim, so
    # a surviving placeholder is user-visible breakage, not a cosmetic issue.
    stray = re.search(PLACEHOLDER, alert["description"])
    if stray:
        fail(f"{name}: description still contains {stray.group(0)!r} after cleaning")
    if not alert["description"]:
        fail(f"{name}: description cleaned away to nothing (upstream: {raw_description!r})")
    return alert


DURATION_UNITS = {"s": 1 / 60, "m": 1, "h": 60, "d": 1440, "w": 10080, "y": 525600}


def parse_duration_minutes(value) -> int:
    """Prometheus duration -> whole minutes, rounded up, minimum 1."""
    if not value:
        return 1
    total = 0.0
    for num, unit in re.findall(r"(\d+)([smhdwy])", str(value)):
        total += int(num) * DURATION_UNITS[unit]
    return max(1, int(total + 0.999)) if total else 1


PACK_README = """# {display} alerts

{blurb}

Alerts live at `packs/{pack}/alerts/<category>/<name>.json`. Current
per-category counts are in [`PACKS.md`](../../PACKS.md), which CI regenerates
from the tree on every merge; the gallery reads `manifest.json`. Neither is
duplicated here, because a count written by hand in a README is a count that
goes stale.

## Provenance

Every alert in this pack is imported from
[awesome-prometheus-alerts](https://github.com/samber/awesome-prometheus-alerts),
whose rules and content are licensed **CC BY 4.0**. See
[`ATTRIBUTION.md`](../../ATTRIBUTION.md) for the full notice, and each alert's
`source` object for the upstream rule name, exporter, page and original
expression.

Do not hand-edit files in this pack: they are regenerated wholesale by
`scripts/import_awesome_prometheus_alerts.py`. Fixes belong upstream, or in
that script's fixup tables.
"""


def write_pack_readme(pack: str) -> None:
    display, blurb = PACK_INFO[pack]
    (PACKS_DIR / pack / "README.md").write_text(
        PACK_README.format(display=display, blurb=blurb, pack=pack)
    )


def iter_rules(data):
    for group in data["groups"]:
        for service in group["services"]:
            for exporter in service.get("exporters") or []:
                for rule in exporter.get("rules") or []:
                    query = rule["query"].strip()
                    if query in QUERY_FIXUPS:
                        rule = dict(rule, query=QUERY_FIXUPS[query])
                        applied_fixups.add(query)
                    yield group["name"], service["name"], exporter["slug"], rule, query


applied_fixups: set[str] = set()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source",
        default=str(ROOT.parent / "awesome-prometheus-alerts" / "_data" / "rules.yml"),
        help="path to the upstream rules.yml",
    )
    args = ap.parse_args()

    src = Path(args.source).expanduser().resolve()
    if not src.is_file():
        fail(f"source not found: {src}")
    data = yaml.safe_load(src.read_text())

    # Pass 1: resolve placement, and find rule names that repeat inside a pack —
    # `<pack>/<name>` is the manifest's stable id, so those must be
    # disambiguated by exporter rather than silently colliding.
    staged = []
    per_pack_names = {}
    for group, service, exporter, rule, upstream_query in iter_rules(data):
        pack = SERVICE_PACK.get(service) or GROUP_PACK.get(group)
        if not pack:
            fail(f"no pack mapping for group '{group}' / service '{service}'")
        category = SERVICE_CATEGORY.get(service) or to_slug(service)
        base = to_name(rule["name"])
        if not base:
            fail(f"rule name slugifies to nothing: {rule['name']!r}")
        staged.append(
            (pack, category, base, group, service, exporter, rule, upstream_query)
        )
        per_pack_names.setdefault(pack, {}).setdefault(base, 0)
        per_pack_names[pack][base] += 1

    # Everything is built and validated BEFORE anything is deleted. The delete
    # is unconditional and wide (13 packs, 1,155 files), so any `fail()` that
    # can fire during conversion must fire while the tree is still intact —
    # otherwise an upstream schema change leaves a half-written library that
    # both the validator and the manifest generator would happily accept.
    built = []
    seen: dict[tuple[str, str], str] = {}
    for pack, category, base, group, service, exporter, rule, upstream_query in staged:
        name = base
        if per_pack_names[pack][base] > 1:
            name = f"{base}_{to_name(exporter)}"
        # Belt and braces: identical rule name AND exporter twice in one pack.
        suffix = 2
        while (pack, name) in seen:
            name = f"{base}_{to_name(exporter)}_{suffix}"
            suffix += 1
        seen[(pack, name)] = f"{pack}/{category}/{base}"

        alert = build_alert(
            rule,
            name=name,
            category=category,
            service=service,
            exporter=exporter,
            group=group,
            promql_bits=to_promql_alert(rule["query"]),
            upstream_query=upstream_query,
        )
        built.append(
            (
                PACKS_DIR / pack / "alerts" / category / f"{name}.json",
                json.dumps(alert, indent=2, ensure_ascii=False) + "\n",
            )
        )

    unused = sorted(set(QUERY_FIXUPS) - applied_fixups)
    if unused:
        fail(
            f"QUERY_FIXUPS entry no longer matches any upstream query (fixed "
            f"upstream? drop it): {unused[0]}"
        )

    # A source file that parses but yields nothing (an empty `groups:`, or an
    # upstream rename of the `rules:` key) would otherwise delete the entire
    # imported library and report success.
    if len(built) < MIN_EXPECTED_ALERTS:
        fail(
            f"only {len(built)} alerts built from {src} — expected at least "
            f"{MIN_EXPECTED_ALERTS}. Refusing to replace the imported packs; "
            "the source file is probably empty or has changed shape."
        )

    for pack in PACKS_OWNED:
        shutil.rmtree(PACKS_DIR / pack, ignore_errors=True)

    for out, payload in built:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload)
    written = len(built)

    for pack in sorted({p for p, *_ in staged}):
        write_pack_readme(pack)

    packs = sorted({p for p, *_ in staged})
    cats = {(p, c) for p, c, *_ in staged}
    normalized = sum(
        1 for *_, r, _ in staged if to_promql_alert(r["query"])[3]
    )
    print(
        f"import: OK — {written} alerts, {len(packs)} packs, {len(cats)} categories "
        f"({normalized} queries normalised, {written - normalized} threshold-split)"
    )


if __name__ == "__main__":
    main()
