# OpenObserve Alert Library

A curated, production-ready collection of alert rules for [OpenObserve](https://openobserve.ai) — organized by domain, each with verified PromQL and SQL queries, notification templates, and test manifests.

---

## What is OpenObserve?

[OpenObserve](https://openobserve.ai) is an open-source, cloud-native observability platform designed for **logs, metrics, and traces at petabyte scale**. It is a unified, self-hostable alternative to the Elasticsearch + Grafana + Prometheus stack — simpler to operate and up to **140× cheaper in storage costs**.

### Core Capabilities

| Capability | Description |
|-----------|-------------|
| **Logs** | Ingest, search, and alert on structured and unstructured log data |
| **Metrics** | Prometheus-compatible metric storage with full PromQL support |
| **Traces** | Distributed tracing via OpenTelemetry |
| **Dashboards** | Built-in visualization — no separate Grafana needed |
| **Alerts** | Rule-based alerting with Slack, PagerDuty, email, and webhook support |
| **SQL Search** | Query any stream (logs or metrics) using familiar SQL syntax |

OpenObserve ingests data via the **OpenTelemetry Collector** and exposes a Prometheus-compatible API, meaning existing PromQL queries and OTel instrumentation work without modification.

---

## How Alerting Works in OpenObserve

Alerts in OpenObserve are **scheduled rules** that periodically evaluate a query and send notifications when conditions are met. Two query types are supported.

### PromQL Alerts (Metrics)

Best for continuous numeric metrics — CPU, memory, latency, error rates.

```
Evaluation flow:
  stream_name  →  PromQL expression  →  promql_condition  →  trigger_condition  →  notification
```

Key alert parameters:

| Parameter | Purpose |
|-----------|---------|
| `stream_name` | The metric stream to query |
| `promql` | PromQL expression to evaluate |
| `promql_condition` | Threshold filter on the result (e.g. `>= 80`) |
| `trigger_condition.period` | Look-back window in minutes |
| `trigger_condition.frequency` | How often to evaluate (minutes) |
| `trigger_condition.threshold` | Min number of matching series needed to fire |
| `trigger_condition.silence` | Cooldown period after firing (minutes) |
| `row_template` | Per-series format string in the notification |
| `destinations` | Slack / webhook / email endpoints to notify |

### SQL Alerts (Logs & Metrics)

Best for event-driven detection — log pattern matching, Kubernetes events, complex aggregations.

```sql
SELECT count(*) as event_count, cluster, namespace
FROM "my_log_stream"
WHERE str_match(level, 'ERROR')
GROUP BY cluster, namespace
HAVING event_count > 10
```

Key SQL functions:

| Function | Use |
|----------|-----|
| `str_match(field, 'value')` | Contains-style filter on a specific field |
| `match_all('value')` | Full-text search across all fields |
| `AVG(value)` | Average a gauge metric over the query window |
| `MAX(value) - MIN(value)` | Approximate `increase()` for counter metrics |

### Notifications

Each destination uses a **template** to format the notification body. The `{rows}` placeholder expands the per-alert `row_template` for each firing series.

```
🚨 *Alert:* high_cpu_utilization
*ClusterName:* production | Node: web-01 | CPU: 91.43%
*ClusterName:* staging | Node: web-02 | CPU: 83.12%
```

---

## Repository Structure

Alerts are organized by **domain** at the top level. Each domain contains exported alert JSON files (importable directly into OpenObserve), test manifests, and documentation.

```
o2-alerts-library/
│
├── README.md                  ← You are here
│
├── k8s/                       ✅ Available
│   ├── README.md              ← Kubernetes-specific docs
│   ├── alerts/                ← Exported alert JSONs organized by category
│   ├── tests/                 ← kubectl manifests to trigger each alert
│   ├── openobserve-alert-library.md
│   └── collected-metrics.md
│
├── openobserve/               🔜 Coming soon — OpenObserve self-monitoring
├── aws/                       🔜 Coming soon
├── databases/                 🔜 Coming soon
└── applications/              🔜 Coming soon
```

---

## Domains

### [Kubernetes](./k8s/) ✅

Full observability of Kubernetes clusters — 76 verified alerts across 12 categories covering nodes, pods, containers, storage, networking, workloads, control plane, security, and more.

→ See [`k8s/README.md`](./k8s/README.md)

### OpenObserve _(coming soon)_

Alerts for monitoring OpenObserve itself — ingester memory and CPU pressure, compactor lag, query latency, WAL growth, storage backend errors, and ingestion pipeline failures. Collected via the built-in `zo_*` metrics exposed on each OpenObserve component's `/metrics` endpoint.

### AWS _(coming soon)_

EC2 instance health, RDS performance, ELB error rates, Lambda throttling, S3 cost anomalies — via the AWS CloudWatch OTel receiver.

### Databases _(coming soon)_

PostgreSQL slow queries, connection pool exhaustion, replication lag — via postgres_exporter and Prometheus autodiscovery.

### Applications _(coming soon)_

HTTP error rate SLOs, P99 latency, queue depth — from any application exposing a `/metrics` endpoint with `prometheus.io/scrape: "true"` annotation.

---

## Setup: Alert Templates and Destinations

Before any alert can send notifications, you need two things configured in OpenObserve: a **template** (how the message is formatted) and a **destination** (where to send it). This applies to all domains in this library.

### Step 1 — Create an Alert Template

A template defines the notification body. It supports `{alert_name}` and `{rows}` placeholders — `{rows}` expands the per-alert `row_template` for each firing series.

**In the OpenObserve UI:**
1. Go to **⚙️ Management → Templates → New Template**
2. Name it (e.g. `k8s_alert_template`)
3. Set type to `HTTP`
4. Paste the body:

```json
{
  "text": "🚨 *Alert:* {alert_name}\n{rows}"
}
```

**Via API:**
```bash
curl -X POST \
  "https://<your-openobserve>/api/default/alerts/templates" \
  -H "Authorization: Basic <base64(user:password)>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "k8s_alert_template",
    "type": "http",
    "body": "{\"text\": \"🚨 *Alert:* {alert_name}\\n{rows}\"}"
  }'
```

**Available template variables:**

| Variable | Value |
|----------|-------|
| `{alert_name}` | Name of the alert rule |
| `{rows}` | All matching series, each formatted by the alert's `row_template` |
| `{org_name}` | Organization name |
| `{stream_name}` | Stream being queried |
| `{alert_type}` | `scheduled` or `realtime` |

The `row_template` on each individual alert controls what appears per row, using label names from the query result:
```
*ClusterName:* {k8s_cluster} | Node: {k8s_node_name} | CPU: {value}%
```

---

### Step 2 — Create an Alert Destination

A destination is the webhook or email endpoint that receives notifications. It must reference a template.

> ⚠️ A destination created **without a template** becomes a pipeline destination and **cannot be used with alert rules**.

**In the OpenObserve UI:**
1. Go to **⚙️ Management → Notification Destinations → New Destination**
2. Name it (e.g. `k8s_alert`)
3. Set type to `HTTP`
4. Enter your webhook URL
5. Select the template from Step 1
6. Set method to `POST`

**Via API (Slack example):**
```bash
curl -X POST \
  "https://<your-openobserve>/api/default/alerts/destinations" \
  -H "Authorization: Basic <base64(user:password)>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "k8s_alert",
    "type": "http",
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "method": "post",
    "template": "k8s_alert_template",
    "headers": { "Content-Type": "application/json" },
    "skip_tls_verify": false
  }'
```

**For email destinations:**
```bash
curl -X POST \
  "https://<your-openobserve>/api/default/alerts/destinations" \
  -H "Authorization: Basic <base64(user:password)>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "k8s_email",
    "type": "email",
    "emails": ["oncall@yourcompany.com"],
    "template": "k8s_alert_template"
  }'
```

**Supported destination types:**

| Type | Use case |
|------|---------|
| `http` | Slack, PagerDuty, Microsoft Teams, any webhook |
| `email` | Email via SMTP |

---

### Step 3 — Import Alert Rules

Each alert in the `alerts/` folder of any domain is an exported JSON file importable directly into OpenObserve. Update the `destinations` field to match your destination name, then import:

```bash
curl -X POST \
  "https://<your-openobserve>/api/default/alerts?folder=<folder_id>" \
  -H "Authorization: Basic <base64(user:password)>" \
  -H "Content-Type: application/json" \
  -d @alerts/node/node_high_cpu_utilization.json
```

Or via the UI: **Alerts → Import → Add Alert**.

---

## Contributing

1. Add a new top-level folder for each new domain (e.g. `aws/`, `databases/`)
2. Include a `README.md`, `alerts/` folder with exported JSONs, and `tests/` folder
3. Verify all queries return real data before committing
4. Document any metrics that cannot be collected and why

---

## License

MIT
