# OpenObserve K8S Alert Creation Status

**Folder:** `mdmosaraf` (ID: `7461312355696140288`)
**Destination:** `O2K8SAlerts`
**Total Alerts:** 75 across 12 categories
**Last Updated:** 2026-05-16

---

## Summary

| # | Category | Total | Done | Pending |
|---|----------|-------|------|---------|
| 1 | Node-Level Alerts | 9 | 10 | 0 |
| 2 | Pod-Level Alerts | 7 | 7 | 0 |
| 3 | Container-Level Alerts | 4 | 4 | 0 |
| 4 | Cluster-Level Alerts | 5 | 4 | 1 |
| 5 | Storage Alerts | 4 | 4 | 0 |
| 6 | Network Alerts | 4 | 4 | 0 |
| 7 | Workload Health Alerts | 7 | 7 | 0 |
| 8 | Control Plane Alerts | 7 | 5 | 2 |
| 9 | Security & Compliance Alerts | 10 | 4 | 6 |
| 10 | Resource Optimization Alerts | 6 | 6 | 0 |
| 11 | Application Performance Alerts | 7 | 3 | 4 |
| 12 | Kubernetes Events Alerts | 5+12 | 17 | 0 |
| | **TOTAL** | **75+12** | **76** | **11** |

---

## 1. Node-Level Alerts ✅ (9/9)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 1 | High Node CPU Usage | Warning | ✅ Created | `node_high_cpu_utilization` (ID: 3DngydddukOMNzI9u6mpGVJ0lTt) |
| 2 | Critical Node CPU Usage | Critical | ✅ Created | `node_critical_cpu_utilization` (ID: 3Dnh0VTJPKZmcyoKKqfGQ0CDGw8) |
| 3 | High Node Memory Usage | Warning | ✅ Created | `node_high_memory_usage` |
| 4 | Critical Node Memory Usage | Critical | ✅ Created | `node_critical_memory_usage` |
| 5 | Node Not Ready | Critical | ✅ Created | `node_not_ready` |
| 6 | Node Disk Pressure | Warning | ✅ Created | `node_disk_pressure` |
| 7 | Node Memory Pressure | Warning | ✅ Created | `node_memory_pressure` |
| 8 | High Node Disk Usage | Warning | ✅ Created | `node_high_disk_usage` |
| 8b | Critical Node Disk Usage | Critical | ✅ Created | `node_critical_disk_usage` |
| 9 | Node Unschedulable | Warning | ✅ Created | `node_unschedulable` |

---

## 2. Pod-Level Alerts ✅ (7/7)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 10 | Pod CrashLoopBackOff | Critical | ✅ Created | `pod_crashloop_backoff` |
| 11 | High Pod Restart Rate | Warning | ✅ Created | `pod_high_restart_rate` |
| 12 | Pod Pending State | Warning | ✅ Created | `pod_pending_too_long` |
| 13 | Pod Failed State | Critical | ✅ Created | `pod_failed_state` |
| 14 | Pod ImagePullBackOff | Warning | ✅ Created | `pod_image_pull_backoff` |
| 15 | Pod OOMKilled | Critical | ✅ Created | `pod_oom_killed` |
| 16 | Pod Evicted | Warning | ✅ Created | `pod_evicted` |

---

## 3. Container-Level Alerts ✅ (4/4)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 17 | Container CPU Near Limit | Warning | ✅ Created | `container_cpu_limit_high` |
| 18 | Container Memory Near Limit | Warning | ✅ Created | `container_memory_near_limit` |
| 19 | Container Not Ready | Warning | ✅ Created | `container_not_ready` |
| 20 | Container Restarted | Info | ✅ Created | `container_restarted` |

---

## 4. Cluster-Level Alerts 🔄 (4/5)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 21 | Cluster CPU Capacity High | Warning | ✅ Created | `cluster_cpu_capacity_high` |
| 22 | Cluster Memory Capacity High | Warning | ✅ Created | `cluster_memory_capacity_high` |
| 23 | Cluster Pod Count High | Warning | ✅ Created | `cluster_pod_count_high` |
| 24 | Certificate Expiration Warning | Warning | ✅ Created | `certificate_expiry_warning` |
| 25 | API Server High Latency | Warning | ✅ Created | `apiserver_high_latency` |

---

## 5. Storage Alerts ✅ (4/4)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 26 | PersistentVolume Failed | Critical | ✅ Created | `pv_failed` |
| 27 | PVC Pending >5min | Warning | ✅ Created | `pvc_pending` |
| 27b | PVC Lost | Critical | ✅ Created | `pvc_lost` |
| 28 | High PV Usage | Warning | ✅ Created | `pv_usage_high` |
| 29 | StorageClass Provisioning Failures | Warning | ⛔ Skipped | Metric not collected by collector |

---

## 6. Network Alerts ✅ (4/4)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 30 | Node Network Errors High | Warning | ✅ Created | `node_network_errors_high` |
| 31 | Service No Ready Endpoints | Critical | ✅ Created | `service_no_ready_endpoints` |
| 32 | DNS Resolution Failures High | Warning | ✅ Created | `dns_resolution_failures_high` |
| 33 | DNS High Latency | Warning | ✅ Created | `dns_high_latency` |

---

## 7. Workload Health Alerts ✅ (7/7)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 34 | Deployment Replica Mismatch | Warning | ✅ Created | `deployment_replica_mismatch` |
| 35 | StatefulSet Replica Mismatch | Warning | ✅ Created | `statefulset_replica_mismatch` |
| 36 | DaemonSet Pods Not Scheduled | Warning | ✅ Created | `daemonset_pods_not_scheduled` |
| 37 | Job Failed | Warning | ✅ Created | `job_failed` |
| 38 | CronJob Missed Schedule | Warning | ✅ Created | `cronjob_missed_schedule` |
| 39 | HPA Unable to Scale | Warning | ✅ Created | `hpa_unable_to_scale` |
| 40 | HPA At Max Replicas | Warning | ✅ Created | `hpa_at_max_replicas` |

---

## 8. Control Plane Alerts 🔄 (5/7)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 41 | etcd High Request Latency | Critical | ⛔ Skipped | etcd not scraped by collector |
| 42 | etcd Database Size Large | Warning | ⛔ Skipped | etcd not scraped by collector |
| 43 | Scheduler Binding Latency High | Warning | ⛔ Skipped | scheduler not scraped by collector |
| 44 | Controller Reconcile Errors High | Warning | ✅ Created | `controller_reconcile_errors_high` |
| 44b | Controller Workqueue Depth High | Warning | ✅ Created | `controller_workqueue_depth_high` |
| 45 | Kubelet Down | Critical | ✅ Covered | Covered by `node_not_ready` |
| 46 | API Server Error Rate High | Critical | ✅ Created | `apiserver_error_rate_high` |
| 46b | API Server Inflight Requests High | Warning | ✅ Created | `apiserver_inflight_requests_high` |
| 46c | Admission Webhook Failures High | Warning | ✅ Created | `admission_webhook_failures_high` |
| 47 | Cloud Provider Rate Limiting | Warning | ⛔ Skipped | cloudprovider metrics not collected |

---

## 9. Security & Compliance Alerts 🔄 (5/10)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 48 | Privileged Container Running | Critical | ⛔ Skipped | securityContext not in kube-state-metrics |
| 49 | Container Running as Root | Warning | ⛔ Skipped | securityContext not in kube-state-metrics |
| 50 | Pod Missing Resource Limits | Warning | ✅ Created | `pod_missing_resource_limits` |
| 51 | Unauthorized API Access High | Critical | ✅ Created | `unauthorized_api_access_high` |
| 52 | Secret Accessed by Suspicious Pod | Warning | ⛔ Skipped | Requires audit logs (not metrics) |
| 53 | Namespace Without Network Policy | Warning | ✅ Created | `namespace_without_network_policy` |
| 54 | Pod Security Policy Violation | Critical | ⛔ Skipped | PSP deprecated/removed in K8s 1.25+ |
| 55 | Image From Untrusted Registry | Warning | ✅ Created | `image_from_untrusted_registry` |
| 56 | ServiceAccount Token Exposure | Critical | ⛔ Skipped | Requires audit logs (not metrics) |
| 57 | Admission Webhook Failures | Critical | ✅ Covered | `admission_webhook_failures_high` (Control Plane) |

---

## 10. Resource Optimization Alerts ✅ (6/6)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 58 | Container CPU Over-Provisioned | Info | ✅ Created | `container_cpu_over_provisioned` |
| 59 | Container Memory Over-Provisioned | Info | ✅ Created | `container_memory_over_provisioned` |
| 60 | Container Resource Under-Requested | Warning | ✅ Created | `container_resource_under_requested` |
| 61 | Node Low Utilization | Info | ✅ Created | `node_low_utilization` |
| 62 | Storage Volume Under-Utilized | Info | ✅ Created | `storage_volume_under_utilized` |
| 63 | Pods Without Resource Requests | Warning | ✅ Created | `pods_without_resource_requests` |

---

## 11. Application Performance Alerts 🔄 (3/7)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 64 | High Application Error Rate | Critical | ⛔ Skipped | Requires app HTTP metrics (prometheus.io/scrape) |
| 65 | High Application Response Latency | Warning | ⛔ Skipped | Requires app HTTP latency metrics |
| 66 | Service Dependency Failure | Critical | ⛔ Skipped | Requires service mesh (Istio/Linkerd) |
| 67 | Slow Database Queries | Warning | ⛔ Skipped | Requires DB exporter metrics |
| 68 | Controller Queue Processing Slow | Warning | ✅ Created | `controller_queue_processing_slow` |
| 69 | Cache Miss Rate High | Warning | ⛔ Skipped | Requires app cache metrics |
| 70 | Go GC Pause High | Warning | ✅ Created | `go_gc_pause_high` |
| 70b | Go GC Rate High | Warning | ✅ Created | `go_gc_rate_high` |

---

## 12. Kubernetes Events Alerts ✅ (5/5)

| # | Alert Name | Severity | Status | OO Name |
|---|-----------|----------|--------|---------|
| 71 | Pod Scheduling Failures Events | Warning | ✅ Created | `pod_scheduling_failures_events` |
| 72 | Image Pull Errors Events | Warning | ✅ Created | `image_pull_errors_events` |
| 73 | Volume Mount Failures Events | Critical | ✅ Created | `volume_mount_failures_events` |
| 74 | Node Condition Change Events | Warning | ✅ Created | `node_condition_change_events` |
| 75 | High Warning Event Rate | Warning | ✅ Created | `high_warning_event_rate` |

---

## Notes

- Metric stream names use `k8s_*` prefix (OpenTelemetry collector format)
- CPU utilization metric: `k8s_node_cpu_utilization` (ratio 0–1)
- Memory usage computed as: `k8s_node_memory_usage / (k8s_node_memory_usage + k8s_node_memory_available)`
- Disk usage computed as: `k8s_node_filesystem_usage / k8s_node_filesystem_capacity`
- PromQL alerts require `conditions: {version: 2, ...}` block in query_condition
- Destination `mdmosaraf_o2` has no template — use `O2K8SAlerts` instead
