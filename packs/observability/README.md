# Observability alerts

The monitoring stack itself — Prometheus, Thanos, Loki, Tempo, Mimir and friends.

Alerts live at `packs/observability/alerts/<category>/<name>.json`. Current
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
