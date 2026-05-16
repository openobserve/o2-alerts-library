# Kubernetes Alerts

Production-ready Kubernetes observability alerts for OpenObserve — 76 verified alerts across 12 categories, built on top of the [OpenObserve Collector](https://github.com/openobserve/openobserve-helm-chart/tree/main/charts/openobserve-collector).

---

## Data Collection

> **How to collect data from your Kubernetes cluster →**
> Deploy the [OpenObserve Collector Helm chart](https://github.com/openobserve/openobserve-helm-chart/tree/main/charts/openobserve-collector).
> Full setup guide: [https://openobserve.ai/docs/ingestion/kubernetes/](https://openobserve.ai/docs/ingestion/kubernetes/)

The [OpenObserve Collector](https://github.com/openobserve/openobserve-helm-chart/tree/main/charts/openobserve-collector) is an OpenTelemetry-based Helm chart that deploys as two components:

| Component | Type | Collects |
|-----------|------|---------|
| **Agent** | DaemonSet (every node) | Container logs, host metrics, kubelet stats |
| **Gateway** | Deployment (cluster-wide) | K8s object events, Prometheus scraping of control plane |

### Metric Sources

| Source | Stream prefix | Key streams |
|--------|--------------|-------------|
| Host metrics (per node) | `system_*` | `system_cpu_utilization`, `system_memory_utilization`, `system_filesystem_usage` |
| Kubelet stats (per pod/container) | `k8s_*` | `k8s_node_cpu_usage`, `k8s_pod_cpu_limit_utilization`, `k8s_container_restarts` |
| Kube-state-metrics | `kube_*` | `kube_pod_status_phase`, `kube_deployment_status_replicas_available`, `kube_node_status_condition` |
| CoreDNS | `coredns_*` | `coredns_dns_responses_total`, `coredns_dns_request_duration_seconds_bucket` |
| kube-apiserver | `apiserver_*` | `apiserver_request_total`, `apiserver_request_duration_seconds_bucket` |
| kube-controller-manager | `controller_runtime_*`, `workqueue_*` | `controller_runtime_reconcile_errors_total`, `workqueue_depth` |
| Kubernetes Events | `k8s_events` (log stream) | All K8s Warning events, object state changes |

> See [`collected-metrics.md`](./collected-metrics.md) for the complete field-level reference.

---

## Setup

Before using these alerts, configure an **Alert Template** and **Alert Destination** in your OpenObserve instance.

→ See the [Setup Guide in the root README](../README.md#setup-alert-templates-and-destinations) for step-by-step instructions (UI + API) for creating templates, destinations, and importing alert rules.

The alerts in this library use:
- **Template:** `k8s_alert_template` — body: `{"text": "🚨 *Alert:* {alert_name}\n{rows}"}`
- **Destination:** `k8s_alert` — HTTP POST to your Slack/webhook URL, using `k8s_alert_template`

---

## Alert Categories

| Category | Alerts | Folder |
|----------|--------|--------|
| Node | 10 | [alerts/node/](./alerts/node/) |
| Pod | 7 | [alerts/pod/](./alerts/pod/) |
| Container | 4 | [alerts/container/](./alerts/container/) |
| Cluster | 5 | [alerts/cluster/](./alerts/cluster/) |
| Storage | 5 | [alerts/storage/](./alerts/storage/) |
| Network | 4 | [alerts/network/](./alerts/network/) |
| Workload | 8 | [alerts/workload/](./alerts/workload/) |
| Control Plane | 6 | [alerts/control-plane/](./alerts/control-plane/) |
| Security | 4 | [alerts/security/](./alerts/security/) |
| Resource Optimization | 5 | [alerts/resource-optimization/](./alerts/resource-optimization/) |
| App Performance | 2 | [alerts/app-performance/](./alerts/app-performance/) |
| K8s Events (SQL) | 16 | [alerts/k8s-events/](./alerts/k8s-events/) |
| **Total** | **76** | |

---

## Alert Reference

The full reference with PromQL queries, SQL equivalents, thresholds, and remediation actions is in:

→ [`openobserve-alert-library.md`](./openobserve-alert-library.md)

---

## Quick Start: Priority Alerts

Deploy these first for immediate cluster protection:

**Priority 1 — Critical Infrastructure**
- `node_not_ready` — node is unreachable
- `oom_killing_events` — kernel OOM killer actively firing
- `coredns_unreachable_events` — all DNS resolution broken
- `node_shutdown_events` — unexpected node shutdown
- `apiserver_error_rate_high` — API server returning 5xx errors

**Priority 2 — Pod Health**
- `pod_crashloop_backoff` — container in CrashLoopBackOff
- `pod_oom_killed` — pod OOMKilled
- `pod_failed_state` — pod permanently failed
- `pod_high_restart_rate` — >5 restarts in 10 minutes

**Priority 3 — Resource Pressure**
- `node_critical_cpu_utilization` — node CPU >90%
- `node_critical_memory_usage` — node memory >95%
- `container_memory_near_limit` — container at 90% of memory limit
- `cluster_cpu_capacity_high` — cluster-wide CPU requests >80%

**Priority 4 — Workload Health**
- `deployment_replica_mismatch` — deployment has unavailable replicas
- `daemonset_pods_not_scheduled` — DaemonSet missing pods on nodes
- `hpa_unable_to_scale` — HPA cannot scale workload

---

## Notification Format

All alerts use the `k8s_alert` destination with the `k8s_alert_template`. Slack notifications look like:

```
🚨 *Alert:* node_high_cpu_utilization
*ClusterName:* o2aks1 | Node: aks-node-1 | CPU: 87.43%
*ClusterName:* production | Node: ip-10-1-2-3 | CPU: 82.15%
```

The `row_template` on each alert controls which labels appear. Node-level alerts use `{k8s_node_name}`, pod-level alerts use `{namespace}` and `{pod}`, event alerts use `{event_name}`.

---

## Files

```
k8s/
├── README.md                        ← This file
├── alerts/                          ← Exported alert JSONs (importable into OpenObserve)
│   ├── node/                        10 alerts
│   ├── pod/                         7 alerts
│   ├── container/                   4 alerts
│   ├── cluster/                     5 alerts
│   ├── storage/                     5 alerts
│   ├── network/                     4 alerts
│   ├── workload/                    8 alerts
│   ├── control-plane/               6 alerts
│   ├── security/                    4 alerts
│   ├── resource-optimization/       5 alerts
│   ├── app-performance/             2 alerts
│   └── k8s-events/                  16 alerts
├── tests/                           ← kubectl manifests to trigger each alert
│   ├── test-pod-alerts.yaml
│   ├── test-container-alerts.yaml
│   ├── test-cluster-alerts.yaml
│   ├── test-storage-alerts.yaml
│   ├── test-network-alerts.yaml
│   ├── test-workload-alerts.yaml
│   ├── test-controlplane-alerts.yaml
│   ├── test-security-alerts.yaml
│   ├── test-resource-optimization-alerts.yaml
│   ├── test-app-performance-alerts.yaml
│   └── test-events-alerts.yaml
├── openobserve-alert-library.md     ← Full reference: PromQL + SQL + descriptions
├── collected-metrics.md             ← Complete metrics reference from the collector
└── alert-creation-status.md        ← Implementation tracker
```

---

## Skipped Alerts

Some alerts cannot be created on managed Kubernetes (AKS, EKS, GKE):

| Alert | Reason |
|-------|--------|
| etcd latency / database size | etcd managed by cloud provider — endpoint not accessible |
| Scheduler latency | Port `:10259` blocked on managed control plane |
| cloudprovider rate limiting | Controller-manager metrics blocked on managed K8s |
| Privileged container / root user | `kube_pod_container_security_context_*` removed in kube-state-metrics v2.x — use [Falco](https://falco.org) |
| Secret / SA token audit | Requires K8s audit logs, not Prometheus metrics |
| HTTP error rate / latency | Requires app-level `prometheus.io/scrape` instrumentation |
| Service mesh metrics | Requires Istio or Linkerd |

These limitations apply equally to AKS, EKS, and GKE. Self-managed clusters (kubeadm, k3s) have full access to all control plane metrics.

---

## Prerequisites

- OpenObserve v0.9+ instance
- [OpenObserve Collector](https://github.com/openobserve/openobserve-helm-chart/tree/main/charts/openobserve-collector) deployed in the cluster
- kube-state-metrics v2.x (bundled with the collector chart)
- A configured alert destination in OpenObserve (Slack, email, or webhook)
