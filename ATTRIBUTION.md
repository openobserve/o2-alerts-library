# Attribution

## awesome-prometheus-alerts

Thirteen of the packs in this library — `applications`, `ci-cd`,
`cloud-providers`, `data-engineering`, `databases`, `infrastructure`,
`message-brokers`, `network-and-security`, `observability`, `orchestrators`,
`proxies-and-service-mesh`, `runtimes` and `storage` — are derived from
**[awesome-prometheus-alerts](https://github.com/samber/awesome-prometheus-alerts)**
by Samuel Berthe and its contributors.

* Source: <https://github.com/samber/awesome-prometheus-alerts> (`_data/rules.yml`)
* Site: <https://samber.github.io/awesome-prometheus-alerts>
* Copyright (c) 2018 Samuel Berthe
* Alert rules and content are licensed under
  [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

CC BY 4.0 permits redistribution and adaptation, including commercially,
provided attribution is given and changes are indicated. Both obligations are
met here:

* **Attribution** — this notice, a provenance section in each derived pack's
  `README.md`, and a per-alert `source` object naming the project, its licence,
  the upstream rule, the exporter it targets and the page it came from.
* **Indication of changes** — every derived alert is a modified work. The
  changes are mechanical and are performed by
  `scripts/import_awesome_prometheus_alerts.py`, which documents each one:

  1. The Prometheus rule is expressed as an OpenObserve alert definition
     (`query_condition` / `trigger_condition` instead of `expr` / `for`).
  2. The threshold is lifted out of the PromQL expression into
     `query_condition.promql_condition`, because OpenObserve evaluates
     `({promql}) {operator} {value}`. Where the threshold cannot be lifted
     safely, the expression is normalised instead — see
     `source.query_normalized` on the alerts affected.
  3. Go template actions in the annotations (`{{ $labels.instance }}`,
     `{{ $value | humanize }}`) are removed from the description, which becomes
     placeholder-free catalogue prose ("Pod {{ $labels.pod }} is crash looping"
     → "Pod is crash looping"), because OpenObserve substitutes row variables
     only into `row_template`. The labels those actions named are carried into
     `row_template` instead, where they do substitute. The unmodified upstream
     description is preserved in `source.upstream_description`.
  4. Rules are regrouped into this library's pack/category layout and given
     library metadata (`title`, `severity`, `tags`, `docs_url`, `source`).

  The unmodified upstream expression and description are preserved verbatim in
  `source.upstream_query` and `source.upstream_description` on every derived
  alert, so the original and the adaptation can always be compared. Where a
  conversion loses something, the file says so: `source.query_normalized`,
  `source.labels_dropped` and `source.period_clamped_from` each name what was
  changed and why.

One upstream expression does not parse as PromQL and is corrected on import;
that correction lives in `QUERY_FIXUPS` in the import script, with its reason.
The script fails the build if a fixup stops matching, so a patch cannot outlive
the defect it was written for.

The `k8s` and `openobserve` packs are original work by OpenObserve Inc. and are
not derived from awesome-prometheus-alerts. This repository as a whole is
licensed CC BY 4.0 (see `LICENSE`), the same licence as the imported material,
so there is no licence boundary between the two — only the additional
requirement to credit Samuel Berthe for the packs listed above.
