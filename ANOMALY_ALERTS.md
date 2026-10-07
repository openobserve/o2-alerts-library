# Anomaly-detection alerts

How to author an anomaly-detection alert for this library. Validation:
`scripts/validate_alerts.py` checks anomaly files (`alert_type:
anomaly_detection`) with `validate_anomaly`; the live create against an
OpenObserve Enterprise build is authoritative.

Anomaly-detection alerts (OpenObserve Enterprise) learn a band per
weekday/weekend × hour of day from a stream's history and fire when the series
leaves it. They complement the scheduled alerts; they do not replace them.
`generate_manifest.py` lists them under `anomaly_alerts` (with
`anomaly_alert_count`), never under `alerts`, and pack and category counts
include scheduled alerts only.

## Location and naming

- Only hand-authored packs: the importer deletes and rewrites every pack it
  owns, so an anomaly file in an imported pack is wiped on the next import.
  Use `k8s` for OpenObserve collector data and `apm` for OpenTelemetry trace
  golden signals (`packs/apm/alerts/traces/`). Pod-log alerts go in
  `k8s/alerts/logs/`.
- Name: snake_case `<signal>_<what>_anomaly`, ending `_anomaly`. The suffix is a
  convention only — `alert_type` is the discriminator (an imported scheduled
  alert is already called `jvm_class_loading_anomaly`).
- Volume alerts that matter both ways are split into `_drop_anomaly`
  (`below`) and `_spike_anomaly` (`above`), so each side has its own severity.

## File format

The file is exactly the v2 create body (`POST /api/v2/{org}/alerts`) plus
catalogue metadata:

| Key | Required | Notes |
|---|---|---|
| `name` | yes | == filename stem; ends `_anomaly` |
| `title` | yes | gallery headline, sentence case |
| `severity` | yes | `info` or `warning` |
| `description` | yes | plain prose, no `{placeholders}`; states signal, direction, unit, scope, any floor/minimum constants, and how to make a per-entity variant |
| `tags` | yes | `anomaly`, the signal (`traces`/`logs`/`k8s-events`/`metrics`) and a topic (`traffic`, `latency`, `errors`, `saturation`, `telemetry-loss`) |
| `source` | yes | `{"project": "openobserve", "license": "CC-BY-4.0"}`, optional `inspired_by` naming Apache-2.0 files only |
| `docs_url` | no | |
| `alert_type` | yes | `"anomaly_detection"` |
| `stream_type`, `stream_name` | yes | |
| `enabled` | yes | must be `true` — a config created disabled never trains |
| `anomaly_config` | yes | engine fields, below |

Forbidden: instance fields (`destinations`, `id`, `org_id`, `owner`, `last_*`,
`updated_at`); scheduled-only fields (`query_condition`, `trigger_condition`,
`row_template`, `is_real_time`, `context_attributes`); `priority` (the
installer derives it from `severity`); legacy budget-mode fields (`percentile`,
`threshold`, `alert_budget_per_day`, `rcf_*`, `level_half_width_seconds`).

`anomaly_config`:

- `query_mode`: `filters` (with a `filters` list, `[]` for none) or
  `custom_sql`. There is no PromQL mode.
- `detection_function`: one of `count avg sum min max p50 p95 p99` (exact
  case); every function except a filters-mode `count` needs
  `detection_function_field`. In `custom_sql` mode use `avg` and set
  `detection_function_field` to the SQL's output column — never `count`, which
  re-triggers the backend's error-population check.
- One series per config: the engine scores one row per time bucket, so query
  whole-stream aggregates and never `GROUP BY` anything but the bucket.
- `custom_sql` must use `histogram(_timestamp, '<histogram_interval>') AS
  time_bucket` with the interval written literally, `GROUP BY time_bucket ORDER
  BY time_bucket`, and must not contain the substrings `drop`, `delete`,
  `update` or `insert` (training rejects them, even inside a column name).
- An error-only `count` is rejected — alert on a ratio in `custom_sql`
  instead, with an absolute floor and a minimum volume written as literals:
  `CASE WHEN COUNT(*) < 50 THEN 0.01 ELSE GREATEST(<bad>/<all>, 0.01) END`.
  The floor covers low-volume buckets that exist; a bucket with no rows at
  all returns no row. Emit a value for every returned bucket (the floor, or
  0) rather than dropping it: a newly missing run of buckets reads as an outage.
- Mostly-zero series are refused at training. Count events with
  `SUM(CASE WHEN <predicate> THEN 1 ELSE 0 END)` over the whole population so
  quiet buckets report a real 0, and check the series is not near-always zero.
- Never alert on a raw cumulative counter.

## Defaults

| Setting | Default | When to deviate |
|---|---|---|
| `histogram_interval` | `5m` | `15m` for sparse event reasons and expensive body scans |
| `schedule_interval` | = histogram | never shorter; longer only to cut query cost |
| `detection_window_seconds` | 3 × histogram (900 for 5m, 2700 for 15m) | must stay ≥ schedule + histogram |
| `alert_window_buckets` / `_fire_pct` / `_recover_pct` | `3` / `60` / `34` for 5m (2 of 3 fires, ≤ 1 of 3 recovers) | 15m: `2` / `100` / `50` |
| `training_window_days` | `28`, stated explicitly | ≥ 21 always |
| `retrain_interval_days` | `7`, stated explicitly | — |
| `band_width` | absent (Auto) | only with a written reason in the PR |
| `alert_direction` | always explicit | see below |

## Severity

- `info` (default): spikes, saturation drifts, event-mix changes, anything
  with a static sibling alert.
- `warning`: user-facing golden signals and telemetry loss — traffic drops,
  error ratio up, p95 latency up, running-pod drop, FailedScheduling surge.
- `critical`: never for anomaly alerts.

## Direction

- Errors, error ratios, latency, saturation, event surges: `above`.
- Telemetry volume, running pods: `below`.
- Traffic: split into `_drop_anomaly` (`below`, warning) and `_spike_anomaly`
  (`above`, info).
- `both` only for "should be stable" aggregates with no side preference.
- Do not add `both` just to catch a stream stopping: missing buckets in a
  normally busy slot raise an absence anomaly on every alert regardless of
  direction.

## Pre-merge checklist

1. File at `packs/<k8s|apm>/alerts/<category>/<name>.json`, name ends
   `_anomaly`, `alert_type` present, `enabled: true`, no forbidden keys.
2. `python3 scripts/validate_alerts.py` passes.
3. The stream and every field used exist with the collector's default
   `values.yaml`, or the description marks the alert conditional.
4. Direction, severity and window follow the rules above; `band_width` absent
   or justified.
5. Not a mostly-zero series and not an error-only count.
6. The description states unit, scope, floors/minimums, and the per-entity
   customisation.
7. Live check against an OpenObserve Enterprise build with data flowing.
   Record the result (accepted / rows per day / trained or `last_error`) in
   the PR description.

   Step (a) creates the exact file: it must return 200 with an `anomaly_id`,
   and a 400 is a defect in the file. A 200 checks configuration only, not that
   the stream or fields exist. Step (b) runs the query the detector runs: put
   the `custom_sql` verbatim in `SQL`, or for filters mode
   `SELECT histogram(_timestamp,'<hi>') AS time_bucket, <fn> AS value FROM <stream> WHERE <filters> GROUP BY time_bucket ORDER BY time_bucket`.
   It must return a non-empty result with the declared numeric column and one
   row per `time_bucket` (about 288 a day at 5m). A config without a
   destination never notifies, so step (c) creates a separate test copy with
   one, leaving the library file destination-free. With at least 100 buckets of
   data, step (d) trains it and reads the outcome; step (e) deletes both
   configs.

   ```bash
   O2=http://localhost:5080; ORG=default; AUTH='-u root@example.com:<password>'
   FILE=path/to/alert.json
   # a)
   ID_A=$(curl -s $AUTH -XPOST "$O2/api/v2/$ORG/alerts?folder=default" \
        -H 'content-type: application/json' --data "@$FILE" | tee /dev/stderr | jq -r .anomaly_id)
   # b)
   NOW=$(($(date +%s)*1000000)); FROM=$((NOW-86400*1000000))
   jq -n --arg sql "$SQL" --argjson s $FROM --argjson e $NOW \
     '{query:{sql:$sql,start_time:$s,end_time:$e,from:0,size:10000}}' |
   curl -s $AUTH -XPOST "$O2/api/$ORG/_search?type=<stream_type>" \
        -H 'content-type: application/json' --data @- | jq '.hits[:5], (.hits|length)'
   # c) the name must differ from the copy created in (a)
   ID_C=$(jq '. + {name: (.name + "_test"), destinations: ["<test_destination>"]}' "$FILE" |
     curl -s $AUTH -XPOST "$O2/api/v2/$ORG/alerts?folder=default" \
        -H 'content-type: application/json' --data @- | tee /dev/stderr | jq -r .anomaly_id)
   # d)
   curl -s $AUTH -XPOST "$O2/api/$ORG/anomaly_detection/$ID_C/train"
   curl -s $AUTH "$O2/api/$ORG/anomaly_detection/$ID_C" | jq '{status,is_trained,last_error}'
   # e)
   for id in "$ID_A" "$ID_C"; do curl -s $AUTH -XDELETE "$O2/api/v2/$ORG/alerts/$id"; done
   ```
