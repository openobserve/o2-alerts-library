# OpenObserve Alert Library for Kubernetes

A comprehensive alert library for monitoring Kubernetes clusters using OpenObserve collector. This library provides production-ready alerts organized by component to achieve full cluster observability.

All alerts use:
- **Destination:** `k8s_alert`
- **Folder:** `mdmosaraf`
- **SQL-based events alerts** query the `k8s_events` log stream

---

## Table of Contents

1. [Node-Level Alerts](#node-level-alerts)
2. [Pod-Level Alerts](#pod-level-alerts)
3. [Container-Level Alerts](#container-level-alerts)
4. [Cluster-Level Alerts](#cluster-level-alerts)
5. [Storage Alerts](#storage-alerts)
6. [Network Alerts](#network-alerts)
7. [Workload Health Alerts](#workload-health-alerts)
8. [Control Plane Alerts](#control-plane-alerts)
9. [Security and Compliance Alerts](#security-and-compliance-alerts)
10. [Resource Optimization Alerts](#resource-optimization-alerts)
11. [Application Performance Alerts](#application-performance-alerts)
12. [Kubernetes Events Alerts](#kubernetes-events-alerts)

---

## Node-Level Alerts

### 1. High Node CPU Usage
**Severity:** Warning
**Description:** Node CPU utilization exceeds 80% for sustained period, indicating potential resource exhaustion.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_node_name,
  FLOOR((1 - AVG(value)) * 10000) / 100 AS cpu_pct
FROM "system_cpu_utilization"
WHERE state = 'idle'
GROUP BY k8s_cluster, k8s_node_name
HAVING cpu_pct >= 80
ORDER BY cpu_pct DESC
```

**PromQL Query:**
```promql
floor((1 - avg by(k8s_node_name, k8s_cluster)(system_cpu_utilization{state='idle'})) * 10000) / 100
```

**OpenObserve Stream:** `system_cpu_utilization`
**Threshold:** >= 80
**Status:** ✅ Created — alert name: `node_cpu_high_warning`
**Action:** Scale workloads or add nodes to cluster

---

### 2. Critical Node CPU Usage
**Severity:** Critical
**Description:** Node CPU utilization exceeds 90%, risking node performance degradation and potential pod evictions.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_node_name,
  FLOOR((1 - AVG(value)) * 10000) / 100 AS cpu_pct
FROM "system_cpu_utilization"
WHERE state = 'idle'
GROUP BY k8s_cluster, k8s_node_name
HAVING cpu_pct >= 90
ORDER BY cpu_pct DESC
```

**PromQL Query:**
```promql
floor((1 - avg by(k8s_node_name, k8s_cluster)(system_cpu_utilization{state='idle'})) * 10000) / 100
```

**OpenObserve Stream:** `system_cpu_utilization`
**Threshold:** >= 90
**Status:** ✅ Created — alert name: `node_cpu_critical`
**Action:** Immediate investigation and capacity planning required

---

### 3. High Node Memory Usage
**Severity:** Warning
**Description:** Node memory utilization exceeds 85%, approaching OOM conditions.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_node_name,
  FLOOR(AVG(value) * 10000) / 100 AS memory_pct
FROM "system_memory_utilization"
WHERE state = 'used'
GROUP BY k8s_cluster, k8s_node_name
HAVING memory_pct >= 85
ORDER BY memory_pct DESC
```

**PromQL Query:**
```promql
floor(system_memory_utilization{state='used'} * 10000) / 100
```

**OpenObserve Stream:** `system_memory_utilization`
**Threshold:** >= 85
**Status:** ✅ Created — alert name: `node_memory_high_warning`
**Action:** Review memory-intensive workloads and consider node scaling

---

### 4. Critical Node Memory Usage
**Severity:** Critical
**Description:** Node memory utilization exceeds 95%, high risk of OOM kills and pod evictions.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_node_name,
  FLOOR(AVG(value) * 10000) / 100 AS memory_pct
FROM "system_memory_utilization"
WHERE state = 'used'
GROUP BY k8s_cluster, k8s_node_name
HAVING memory_pct >= 95
ORDER BY memory_pct DESC
```

**PromQL Query:**
```promql
floor(system_memory_utilization{state='used'} * 10000) / 100
```

**OpenObserve Stream:** `system_memory_utilization`
**Threshold:** >= 95
**Status:** ✅ Created — alert name: `node_memory_critical`
**Action:** Immediate intervention to prevent OOM kills

---

### 5. Node Not Ready
**Severity:** Critical
**Description:** Node is in NotReady state, unable to schedule new pods or run existing workloads properly.

**SQL Query:**
```sql
SELECT k8s_cluster, node, condition, status,
  AVG(value) AS val
FROM "kube_node_status_condition"
WHERE condition = 'Ready' AND status = 'true'
GROUP BY k8s_cluster, node, condition, status
HAVING val <= 0
```

**PromQL Query:**
```promql
kube_node_status_condition{condition='Ready',status='true'}
```

**OpenObserve Stream:** `kube_node_status_condition`
**Threshold:** <= 0
**Note:** Row template uses `{node}` label (from kube-state-metrics, not `k8s_node_name`). The SQL HAVING checks that a node reported as Ready has val=0, meaning it is not ready.
**Status:** ✅ Created — alert name: `node_not_ready`
**Action:** Check node health, kubelet logs, and network connectivity

---

### 6. Node Disk Pressure
**Severity:** Warning
**Description:** Node is experiencing disk pressure, which may lead to pod evictions.

**SQL Query:**
```sql
SELECT k8s_cluster, node, condition,
  AVG(value) AS val
FROM "kube_node_status_condition"
WHERE condition = 'DiskPressure' AND status = 'true'
GROUP BY k8s_cluster, node, condition
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_node_status_condition{condition='DiskPressure',status='true'}
```

**OpenObserve Stream:** `kube_node_status_condition`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `node_disk_pressure`
**Action:** Clean up unused images, logs, and temporary files

---

### 7. Node Memory Pressure
**Severity:** Warning
**Description:** Node is experiencing memory pressure, risking pod evictions.

**SQL Query:**
```sql
SELECT k8s_cluster, node, condition,
  AVG(value) AS val
FROM "kube_node_status_condition"
WHERE condition = 'MemoryPressure' AND status = 'true'
GROUP BY k8s_cluster, node, condition
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_node_status_condition{condition='MemoryPressure',status='true'}
```

**OpenObserve Stream:** `kube_node_status_condition`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `node_memory_pressure`
**Action:** Review memory limits and requests for pods on the node

---

### 8. High Node Disk Usage
**Severity:** Warning
**Description:** Node filesystem usage exceeds 80%, risking storage exhaustion.

**SQL Query:**
```sql
SELECT u.k8s_cluster, u.k8s_node_name,
  FLOOR(AVG(u.value) / AVG(c.value) * 10000) / 100 AS disk_pct
FROM "k8s_node_filesystem_usage" u
JOIN "k8s_node_filesystem_capacity" c
  ON u.k8s_node_name = c.k8s_node_name
GROUP BY u.k8s_cluster, u.k8s_node_name
HAVING disk_pct >= 80
ORDER BY disk_pct DESC
```

**PromQL Query:**
```promql
floor(k8s_node_filesystem_usage / k8s_node_filesystem_capacity * 10000) / 100
```

**OpenObserve Stream:** `k8s_node_filesystem_usage`
**Threshold:** >= 80
**Note:** The JOIN on `k8s_node_name` correlates used vs capacity bytes per node. Both streams must be present in the query window.
**Status:** ✅ Created — alert name: `node_disk_usage_high_warning`
**Action:** Clean up or expand disk capacity

---

### 8b. Critical Node Disk Usage
**Severity:** Critical
**Description:** Node filesystem usage exceeds 90%, imminent risk of storage exhaustion and node failure.

**SQL Query:**
```sql
SELECT u.k8s_cluster, u.k8s_node_name,
  FLOOR(AVG(u.value) / AVG(c.value) * 10000) / 100 AS disk_pct
FROM "k8s_node_filesystem_usage" u
JOIN "k8s_node_filesystem_capacity" c
  ON u.k8s_node_name = c.k8s_node_name
GROUP BY u.k8s_cluster, u.k8s_node_name
HAVING disk_pct >= 90
ORDER BY disk_pct DESC
```

**PromQL Query:**
```promql
floor(k8s_node_filesystem_usage / k8s_node_filesystem_capacity * 10000) / 100
```

**OpenObserve Stream:** `k8s_node_filesystem_usage`
**Threshold:** >= 90
**Status:** ✅ Created — alert name: `node_disk_usage_critical`
**Action:** Immediately expand disk capacity or remove data to prevent node failure

---

### 9. Node Unschedulable
**Severity:** Warning
**Description:** Node is marked as unschedulable, preventing new pod placements.

**SQL Query:**
```sql
SELECT k8s_cluster, node, key, effect,
  AVG(value) AS val
FROM "kube_node_spec_taint"
WHERE key = 'node.kubernetes.io/unschedulable'
  AND effect = 'NoSchedule'
GROUP BY k8s_cluster, node, key, effect
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_node_spec_taint{key='node.kubernetes.io/unschedulable', effect='NoSchedule'}
```

**OpenObserve Stream:** `kube_node_spec_taint`
**Threshold:** >= 1
**Note:** `kube_node_spec_unschedulable` is not available in this collector configuration; the `node.kubernetes.io/unschedulable` taint is used as a proxy — it is set automatically when a node is cordoned.
**Status:** ✅ Created — alert name: `node_unschedulable`
**Action:** Verify if cordoned intentionally or investigate node issues

---

## Pod-Level Alerts

### 10. Pod CrashLoopBackOff
**Severity:** Critical
**Description:** Pod is repeatedly crashing and restarting, indicating application or configuration issues.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, container, reason
FROM "kube_pod_container_status_waiting_reason"
WHERE reason = 'CrashLoopBackOff'
  AND value >= 1
GROUP BY k8s_cluster, namespace, pod, container, reason
```

**PromQL Query:**
```promql
kube_pod_container_status_waiting_reason{reason='CrashLoopBackOff'}
```

**OpenObserve Stream:** `kube_pod_container_status_waiting_reason`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pod_crashloopbackoff`
**Action:** Check pod logs, resource limits, and application configuration

---

### 11. High Pod Restart Rate
**Severity:** Warning
**Description:** Pod has restarted multiple times in a short period, indicating instability.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name, k8s_container_name,
  MAX(value) - MIN(value) AS restart_increase
FROM "k8s_container_restarts"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name, k8s_container_name
HAVING restart_increase >= 5
ORDER BY restart_increase DESC
```

**PromQL Query:**
```promql
round(increase(k8s_container_restarts[10m]))
```

**OpenObserve Stream:** `k8s_container_restarts`
**Threshold:** >= 5
**Note:** `MAX(value) - MIN(value)` approximates `increase()` over the query window. Set the alert window to 10 minutes to match the PromQL intent. `round()` is required in PromQL — `increase()` returns fractional values due to scrape alignment; rounding gives accurate integer restart counts.
**Status:** ✅ Created — alert name: `pod_restart_rate_high`
**Action:** Investigate pod logs and application health

---

### 12. Pod Pending State
**Severity:** Warning
**Description:** Pod remains in Pending state for more than 5 minutes, unable to be scheduled on any node.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, phase,
  AVG(value) AS val
FROM "kube_pod_status_phase"
WHERE phase = 'Pending'
GROUP BY k8s_cluster, namespace, pod, phase
HAVING val >= 1
```

**PromQL Query:**
```promql
min_over_time(kube_pod_status_phase{phase='Pending'}[5m])
```

**OpenObserve Stream:** `kube_pod_status_phase`
**Threshold:** >= 1
**Note:** `min_over_time` in PromQL ensures the pod has been continuously Pending for the full 5-minute window. In SQL, set the alert evaluation window to 5 minutes — AVG=1 means the pod was Pending throughout.
**Status:** ✅ Created — alert name: `pod_pending_long`
**Action:** Check resource requests, node capacity, and affinity rules

---

### 13. Pod Failed State
**Severity:** Critical
**Description:** Pod has entered Failed state and is not running.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, phase,
  AVG(value) AS val
FROM "kube_pod_status_phase"
WHERE phase = 'Failed'
GROUP BY k8s_cluster, namespace, pod, phase
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_pod_status_phase{phase='Failed'}
```

**OpenObserve Stream:** `kube_pod_status_phase`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pod_failed`
**Action:** Review pod events and logs to determine failure cause

---

### 14. Pod ImagePullBackOff
**Severity:** Warning
**Description:** Pod cannot pull container image, preventing pod startup.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, container, reason
FROM "kube_pod_container_status_waiting_reason"
WHERE reason IN ('ImagePullBackOff', 'ErrImagePull')
  AND value >= 1
GROUP BY k8s_cluster, namespace, pod, container, reason
```

**PromQL Query:**
```promql
kube_pod_container_status_waiting_reason{reason=~'ImagePullBackOff|ErrImagePull'}
```

**OpenObserve Stream:** `kube_pod_container_status_waiting_reason`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pod_imagepullbackoff`
**Action:** Verify image name, registry access, and credentials

---

### 15. Pod OOMKilled
**Severity:** Critical
**Description:** Pod container was killed due to out-of-memory condition.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, container, reason
FROM "kube_pod_container_status_terminated_reason"
WHERE reason = 'OOMKilled'
  AND value >= 1
GROUP BY k8s_cluster, namespace, pod, container, reason
```

**PromQL Query:**
```promql
kube_pod_container_status_terminated_reason{reason='OOMKilled'}
```

**OpenObserve Stream:** `kube_pod_container_status_terminated_reason`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pod_oomkilled`
**Action:** Increase memory limits or optimize application memory usage

---

### 16. Pod Evicted
**Severity:** Warning
**Description:** Pod was evicted from node due to resource pressure.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, reason,
  AVG(value) AS val
FROM "kube_pod_status_reason"
WHERE reason = 'Evicted'
GROUP BY k8s_cluster, namespace, pod, reason
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_pod_status_reason{reason='Evicted'}
```

**OpenObserve Stream:** `kube_pod_status_reason`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pod_evicted`
**Action:** Review node resource usage and pod resource requests

---

## Container-Level Alerts

### 17. High Container CPU Throttling
**Severity:** Warning
**Description:** Container CPU usage is near its configured limit, acting as a proxy for CPU throttling and impacting application performance.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name,
  FLOOR(AVG(value) * 10000) / 100 AS cpu_limit_pct
FROM "k8s_pod_cpu_limit_utilization"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name
HAVING cpu_limit_pct >= 80
ORDER BY cpu_limit_pct DESC
```

**PromQL Query:**
```promql
floor(k8s_pod_cpu_limit_utilization * 10000) / 100
```

**OpenObserve Stream:** `k8s_pod_cpu_limit_utilization`
**Threshold:** >= 80
**Note:** `container_cpu_cfs_throttled_seconds` is not collected by this collector configuration. Pod CPU limit utilization (>= 80% of limit) is used as a proxy to detect containers at risk of throttling.
**Status:** ✅ Created — alert name: `container_cpu_near_limit`
**Action:** Review and adjust CPU limits or optimize application

---

### 18. Container Memory Usage Near Limit
**Severity:** Warning
**Description:** Container memory usage is approaching its configured limit.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name,
  FLOOR(AVG(value) * 10000) / 100 AS memory_limit_pct
FROM "k8s_pod_memory_limit_utilization"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name
HAVING memory_limit_pct >= 90
ORDER BY memory_limit_pct DESC
```

**PromQL Query:**
```promql
floor(k8s_pod_memory_limit_utilization * 10000) / 100
```

**OpenObserve Stream:** `k8s_pod_memory_limit_utilization`
**Threshold:** >= 90
**Status:** ✅ Created — alert name: `container_memory_near_limit`
**Action:** Increase memory limits or investigate memory leaks

---

### 19. Container Not Ready
**Severity:** Warning
**Description:** Container is not passing readiness probes for more than 5 minutes.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, container,
  AVG(value) AS val
FROM "kube_pod_container_status_ready"
GROUP BY k8s_cluster, namespace, pod, container
HAVING val <= 0
```

**PromQL Query:**
```promql
min_over_time(kube_pod_container_status_ready[5m])
```

**OpenObserve Stream:** `kube_pod_container_status_ready`
**Threshold:** <= 0
**Note:** Set the alert evaluation window to 5 minutes — AVG=0 means the container was not ready throughout the window.
**Status:** ✅ Created — alert name: `container_not_ready`
**Action:** Check readiness probe configuration and application health

---

### 20. Container Restart
**Severity:** Info
**Description:** Container has restarted, which may indicate transient issues.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, container,
  MAX(value) - MIN(value) AS restart_increase
FROM "kube_pod_container_status_restarts_total"
GROUP BY k8s_cluster, namespace, pod, container
HAVING restart_increase >= 1
ORDER BY restart_increase DESC
```

**PromQL Query:**
```promql
round(increase(kube_pod_container_status_restarts_total[5m]))
```

**OpenObserve Stream:** `kube_pod_container_status_restarts_total`
**Threshold:** >= 1
**Note:** `MAX(value) - MIN(value)` approximates `increase()` over the query window. Set alert window to 5 minutes.
**Status:** ✅ Created — alert name: `container_restarted`
**Action:** Monitor for pattern and investigate if frequent

---

## Cluster-Level Alerts

### 21. Low Cluster CPU Capacity
**Severity:** Warning
**Description:** Cluster-wide allocatable CPU is running low, limiting scheduling capacity.

**SQL Query:**
```sql
-- Step 1: Get total CPU requested per cluster
-- Step 2: Get total allocatable CPU per cluster
-- Use two separate queries and compare, or use the JOIN below
SELECT r.k8s_cluster,
  FLOOR(SUM(r.value) / SUM(a.value) * 10000) / 100 AS cpu_request_pct
FROM "kube_pod_container_resource_requests" r
JOIN "kube_node_status_allocatable" a
  ON r.k8s_cluster = a.k8s_cluster
WHERE r.resource = 'cpu' AND a.resource = 'cpu'
GROUP BY r.k8s_cluster
HAVING cpu_request_pct >= 80
```

**PromQL Query:**
```promql
floor(sum by(k8s_cluster)(kube_pod_container_resource_requests{resource='cpu'}) / sum by(k8s_cluster)(kube_node_status_allocatable{resource='cpu'}) * 10000) / 100
```

**OpenObserve Stream:** `kube_pod_container_resource_requests`, `kube_node_status_allocatable`
**Threshold:** >= 80
**Note:** Cross-stream JOINs on cluster-level aggregations can be slow. If this query times out, run the two sub-queries separately and compare: `SELECT k8s_cluster, SUM(value) FROM "kube_pod_container_resource_requests" WHERE resource='cpu' GROUP BY k8s_cluster` vs `SELECT k8s_cluster, AVG(value) FROM "kube_node_status_allocatable" WHERE resource='cpu' GROUP BY k8s_cluster, node`.
**Status:** ✅ Created — alert name: `cluster_cpu_capacity_low`
**Action:** Plan for cluster expansion

---

### 22. Low Cluster Memory Capacity
**Severity:** Warning
**Description:** Cluster-wide allocatable memory is running low.

**SQL Query:**
```sql
SELECT r.k8s_cluster,
  FLOOR(SUM(r.value) / SUM(a.value) * 10000) / 100 AS memory_request_pct
FROM "kube_pod_container_resource_requests" r
JOIN "kube_node_status_allocatable" a
  ON r.k8s_cluster = a.k8s_cluster
WHERE r.resource = 'memory' AND a.resource = 'memory'
GROUP BY r.k8s_cluster
HAVING memory_request_pct >= 80
```

**PromQL Query:**
```promql
floor(sum by(k8s_cluster)(kube_pod_container_resource_requests{resource='memory'}) / sum by(k8s_cluster)(kube_node_status_allocatable{resource='memory'}) * 10000) / 100
```

**OpenObserve Stream:** `kube_pod_container_resource_requests`, `kube_node_status_allocatable`
**Threshold:** >= 80
**Note:** Same caveat as #21 — cross-stream JOINs may be slow; run sub-queries separately if needed.
**Status:** ✅ Created — alert name: `cluster_memory_capacity_low`
**Action:** Plan for cluster expansion or optimize workload requests

---

### 23. High Number of Pods
**Severity:** Warning
**Description:** Total pod count approaching cluster or node limits.

**SQL Query:**
```sql
-- Pod count per cluster (compare against known pod capacity)
SELECT k8s_cluster,
  COUNT(DISTINCT pod) AS pod_count
FROM "kube_pod_info"
GROUP BY k8s_cluster
HAVING pod_count >= 900
```

**PromQL Query:**
```promql
floor(count by(k8s_cluster)(kube_pod_info) / sum by(k8s_cluster)(kube_node_status_allocatable{resource='pods'}) * 10000) / 100
```

**OpenObserve Stream:** `kube_pod_info`, `kube_node_status_allocatable`
**Threshold:** >= 90
**Note:** The PromQL computes pod count as a % of allocatable pod slots. In SQL, `COUNT(DISTINCT pod)` gives a reliable pod count per cluster. Adjust the HAVING threshold to match your cluster's allocatable pod limit (e.g., `>= 900` for a 1000-pod-limit cluster). The `kube_node_status_allocatable` for `pods` resource can be queried separately to get the per-cluster pod ceiling.
**Status:** ✅ Created — alert name: `cluster_pod_count_high`
**Action:** Review pod density and plan scaling

---

### 24. Certificate Expiration Warning
**Severity:** Warning
**Description:** Kubernetes API certificates are approaching expiration (within 30 days).

**SQL Query:**
```sql
SELECT k8s_cluster, le,
  AVG(value) AS cert_expiry_count
FROM "apiserver_client_certificate_expiration_seconds_bucket"
WHERE le = '2592000'
GROUP BY k8s_cluster, le
HAVING cert_expiry_count > 0
```

**PromQL Query:**
```promql
sum by(k8s_cluster)(apiserver_client_certificate_expiration_seconds_bucket{le='2592000'})
```

**OpenObserve Stream:** `apiserver_client_certificate_expiration_seconds_bucket`
**Threshold:** > 0
**Note:** Requires adding `apiserver_client_certificate_expiration_seconds.*` to the collector's `metric_relabel_configs` allowlist. The `le='2592000'` bucket counts certificates expiring within 30 days (2592000 seconds).
**Status:** ✅ Created — alert name: `cert_expiry_warning`
**Action:** Plan certificate rotation

---

### 25. API Server High Latency
**Severity:** Warning
**Description:** API server request latency P99 exceeds 1 second, impacting cluster operations.

**SQL Query:**
```sql
-- Approximate: count requests that fell in buckets <= 1s vs total
-- A high count of requests in the le='1' bucket that is NOT growing
-- fast relative to total indicates p99 > 1s
SELECT k8s_cluster, verb, resource,
  MAX(value) - MIN(value) AS requests_under_1s
FROM "apiserver_request_duration_seconds_bucket"
WHERE le = '1'
GROUP BY k8s_cluster, verb, resource
ORDER BY requests_under_1s ASC
LIMIT 20
```

**PromQL Query:**
```promql
histogram_quantile(0.99, sum by(k8s_cluster, verb, resource, le)(rate(apiserver_request_duration_seconds_bucket[5m])))
```

**OpenObserve Stream:** `apiserver_request_duration_seconds_bucket`
**Threshold:** >= 1
**Note:** True `histogram_quantile` is not possible in SQL. The SQL above shows request growth in the <=1s bucket; low or zero growth here while total requests are high indicates high-latency requests dominating. For a production alert, use the PromQL version with a scheduled PromQL alert.
**Status:** ✅ Created — alert name: `apiserver_latency_high`
**Action:** Investigate API server load and etcd performance

---

## Storage Alerts

### 26. PersistentVolume Failed
**Severity:** Critical
**Description:** PersistentVolume is in Failed state, data access issues likely.

**SQL Query:**
```sql
SELECT k8s_cluster, persistentvolume, phase,
  AVG(value) AS val
FROM "kube_persistentvolume_status_phase"
WHERE phase = 'Failed'
GROUP BY k8s_cluster, persistentvolume, phase
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_persistentvolume_status_phase{phase='Failed'}
```

**OpenObserve Stream:** `kube_persistentvolume_status_phase`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pv_failed`
**Action:** Check storage backend and PV configuration

---

### 27. PersistentVolumeClaim Pending
**Severity:** Warning
**Description:** PVC remains in Pending state for more than 5 minutes, unable to bind to a PV.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, persistentvolumeclaim, phase,
  AVG(value) AS val
FROM "kube_persistentvolumeclaim_status_phase"
WHERE phase = 'Pending'
GROUP BY k8s_cluster, namespace, persistentvolumeclaim, phase
HAVING val >= 1
```

**PromQL Query:**
```promql
min_over_time(kube_persistentvolumeclaim_status_phase{phase='Pending'}[5m])
```

**OpenObserve Stream:** `kube_persistentvolumeclaim_status_phase`
**Threshold:** >= 1
**Note:** Set the alert evaluation window to 5 minutes — AVG=1 means the PVC was Pending throughout, matching the `min_over_time` intent.
**Status:** ✅ Created — alert name: `pvc_pending_long`
**Action:** Check PV availability and storage class configuration

---

### 27b. PersistentVolumeClaim Lost
**Severity:** Critical
**Description:** PVC is in Lost state, meaning the bound PV no longer exists. Data may be inaccessible.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, persistentvolumeclaim, phase,
  AVG(value) AS val
FROM "kube_persistentvolumeclaim_status_phase"
WHERE phase = 'Lost'
GROUP BY k8s_cluster, namespace, persistentvolumeclaim, phase
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_persistentvolumeclaim_status_phase{phase='Lost'}
```

**OpenObserve Stream:** `kube_persistentvolumeclaim_status_phase`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `pvc_lost`
**Action:** Investigate PV deletion and restore from backup if necessary

---

### 28. High PersistentVolume Usage
**Severity:** Warning
**Description:** PersistentVolume usage exceeds 85%, risking storage exhaustion.

**SQL Query:**
```sql
SELECT u.k8s_cluster, u.namespace, u.persistentvolumeclaim,
  FLOOR(AVG(u.value) / AVG(c.value) * 10000) / 100 AS pv_usage_pct
FROM "kubelet_volume_stats_used_bytes" u
JOIN "kubelet_volume_stats_capacity_bytes" c
  ON u.namespace = c.namespace
  AND u.persistentvolumeclaim = c.persistentvolumeclaim
GROUP BY u.k8s_cluster, u.namespace, u.persistentvolumeclaim
HAVING pv_usage_pct >= 85
ORDER BY pv_usage_pct DESC
```

**PromQL Query:**
```promql
floor(kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 10000) / 100
```

**OpenObserve Stream:** `kubelet_volume_stats_used_bytes`
**Threshold:** >= 85
**Note:** The JOIN correlates used vs capacity bytes per PVC. If the query returns no results, it may be because no PVCs are currently mounted/active in the query window.
**Status:** ✅ Created — alert name: `pv_usage_high`
**Action:** Expand volume or clean up data

---

### 29. StorageClass Provisioning Failures
**Severity:** Warning
**Description:** Storage class is experiencing provisioning failures.

**SQL Query:** Not applicable — metric not collected

**PromQL Query:** Not applicable — metric not collected

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — `storage_operation_duration_seconds_count` is not collected by the openobserve-collector in this configuration
**Action:** Check storage backend connectivity and quota

---

## Network Alerts

### 30. High Node Network Error Rate
**Severity:** Warning
**Description:** Node network error rate exceeds 10 errors per second, indicating network issues.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_node_name, direction, interface,
  (MAX(value) - MIN(value)) / 300.0 AS error_rate_per_sec
FROM "k8s_node_network_errors"
GROUP BY k8s_cluster, k8s_node_name, direction, interface
HAVING error_rate_per_sec > 10
ORDER BY error_rate_per_sec DESC
```

**PromQL Query:**
```promql
rate(k8s_node_network_errors[5m])
```

**OpenObserve Stream:** `k8s_node_network_errors`
**Threshold:** > 10
**Note:** `(MAX-MIN) / 300` approximates `rate()[5m]` for a 5-minute window (300 seconds). Adjust the divisor to match your alert evaluation window in seconds.
**Status:** ✅ Created — alert name: `node_network_errors_high`
**Action:** Investigate network configuration and CNI plugin

---

### 31. Service No Ready Endpoints
**Severity:** Critical
**Description:** Service has no available (ready) endpoints, meaning all traffic will fail.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, endpoint,
  COUNT(*) AS not_ready_count
FROM "kube_endpoint_address"
WHERE ready = 'false' AND value >= 1
GROUP BY k8s_cluster, namespace, endpoint
HAVING not_ready_count >= 1
```

**PromQL Query:**
```promql
count by(namespace, endpoint, k8s_cluster)(kube_endpoint_address{ready='false'}) unless count by(namespace, endpoint, k8s_cluster)(kube_endpoint_address{ready='true'})
```

**OpenObserve Stream:** `kube_endpoint_address`
**Threshold:** >= 1
**Note:** The PromQL `unless` operator (set subtraction) cannot be replicated in SQL with a single query. The SQL above detects endpoints with not-ready addresses. For a more precise check (no ready endpoints at all), run an additional query to cross-reference: `SELECT endpoint FROM "kube_endpoint_address" WHERE ready='true' AND value>=1`. If an endpoint appears in the not-ready query but NOT in the ready query, all endpoints are down.
**Status:** ✅ Created — alert name: `service_no_ready_endpoints`
**Action:** Check pod selectors and pod health

---

### 32. DNS Resolution Failures
**Severity:** Warning
**Description:** DNS error response rate exceeds 10 per second within the cluster.

**SQL Query:**
```sql
SELECT k8s_cluster, server, zone, rcode,
  (MAX(value) - MIN(value)) / 300.0 AS error_rate_per_sec
FROM "coredns_dns_responses_total"
WHERE rcode != 'NOERROR'
GROUP BY k8s_cluster, server, zone, rcode
HAVING error_rate_per_sec > 10
ORDER BY error_rate_per_sec DESC
```

**PromQL Query:**
```promql
floor(sum by(k8s_cluster, server, zone)(rate(coredns_dns_responses_total{rcode!='NOERROR'}[5m])) * 100) / 100
```

**OpenObserve Stream:** `coredns_dns_responses_total`
**Threshold:** > 10
**Note:** `(MAX-MIN) / 300` approximates `rate()[5m]`. Adjust divisor to match your alert evaluation window in seconds.
**Status:** ✅ Created — alert name: `dns_resolution_failures`
**Action:** Check CoreDNS pods and configuration

---

### 33. DNS High Latency
**Severity:** Warning
**Description:** CoreDNS P99 request latency exceeds 500ms, impacting service discovery.

**SQL Query:**
```sql
-- Approximate: growth in requests completing within 0.5s bucket
-- Low bucket growth vs total growth indicates high-latency DNS
SELECT k8s_cluster, server, zone,
  MAX(value) - MIN(value) AS requests_under_500ms
FROM "coredns_dns_request_duration_seconds_bucket"
WHERE le = '0.5'
GROUP BY k8s_cluster, server, zone
ORDER BY requests_under_500ms ASC
```

**PromQL Query:**
```promql
floor(histogram_quantile(0.99, sum by(k8s_cluster, server, le)(rate(coredns_dns_request_duration_seconds_bucket[5m]))) * 100) / 100
```

**OpenObserve Stream:** `coredns_dns_request_duration_seconds_bucket`
**Threshold:** > 0.5
**Note:** True `histogram_quantile` is not possible in SQL. The SQL above shows bucket growth for requests completing under 500ms. Low or stagnant growth in this bucket while DNS traffic is active indicates P99 > 500ms. Use the PromQL alert for precision.
**Status:** ✅ Created — alert name: `dns_latency_high`
**Action:** Check CoreDNS resource limits and upstream resolver performance

---

## Workload Health Alerts

### 34. Deployment Replica Mismatch
**Severity:** Warning
**Description:** Deployment has fewer available replicas than desired.

**SQL Query:**
```sql
SELECT spec.k8s_cluster, spec.namespace, spec.deployment,
  AVG(spec.value) AS desired,
  AVG(avail.value) AS available
FROM "kube_deployment_spec_replicas" spec
JOIN "kube_deployment_status_replicas_available" avail
  ON spec.namespace = avail.namespace
  AND spec.deployment = avail.deployment
GROUP BY spec.k8s_cluster, spec.namespace, spec.deployment
HAVING desired > available
ORDER BY desired DESC
```

**PromQL Query:**
```promql
kube_deployment_spec_replicas - kube_deployment_status_replicas_available > 0
```

**OpenObserve Stream:** `kube_deployment_spec_replicas`, `kube_deployment_status_replicas_available`
**Threshold:** >= 1
**Note:** The JOIN uses `spec.` prefix on `k8s_cluster` to avoid the "ambiguous field" error. AVG values may show fractional differences due to time-series averaging over the window; `desired > available` catches any gap.
**Status:** ✅ Created — alert name: `deployment_replica_mismatch`
**Action:** Check pod status and events

---

### 35. StatefulSet Replica Mismatch
**Severity:** Warning
**Description:** StatefulSet has fewer ready replicas than desired.

**SQL Query:**
```sql
SELECT spec.k8s_cluster, spec.namespace, spec.statefulset,
  AVG(spec.value) AS desired,
  AVG(ready.value) AS ready_count
FROM "kube_statefulset_replicas" spec
JOIN "kube_statefulset_status_replicas_ready" ready
  ON spec.namespace = ready.namespace
  AND spec.statefulset = ready.statefulset
GROUP BY spec.k8s_cluster, spec.namespace, spec.statefulset
HAVING desired > ready_count
ORDER BY desired DESC
```

**PromQL Query:**
```promql
kube_statefulset_replicas - kube_statefulset_status_replicas_ready > 0
```

**OpenObserve Stream:** `kube_statefulset_replicas`, `kube_statefulset_status_replicas_ready`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `statefulset_replica_mismatch`
**Action:** Check pod status, PVC availability, and startup sequence

---

### 36. DaemonSet Missing Pods
**Severity:** Warning
**Description:** DaemonSet is missing pods on some nodes.

**SQL Query:**
```sql
SELECT desired.k8s_cluster, desired.namespace, desired.daemonset,
  AVG(desired.value) AS desired_count,
  AVG(ready.value) AS ready_count
FROM "kube_daemonset_status_desired_number_scheduled" desired
JOIN "kube_daemonset_status_number_ready" ready
  ON desired.namespace = ready.namespace
  AND desired.daemonset = ready.daemonset
GROUP BY desired.k8s_cluster, desired.namespace, desired.daemonset
HAVING desired_count > ready_count
ORDER BY desired_count DESC
```

**PromQL Query:**
```promql
kube_daemonset_status_desired_number_scheduled - kube_daemonset_status_number_ready > 0
```

**OpenObserve Stream:** `kube_daemonset_status_desired_number_scheduled`, `kube_daemonset_status_number_ready`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `daemonset_missing_pods`
**Action:** Check node selectors, taints, and tolerations

---

### 37. Job Failed
**Severity:** Warning
**Description:** Kubernetes Job has failed to complete successfully.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, job_name,
  AVG(value) AS val
FROM "kube_job_failed"
GROUP BY k8s_cluster, namespace, job_name
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_job_failed
```

**OpenObserve Stream:** `kube_job_failed`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `job_failed`
**Action:** Check job logs and pod events

---

### 38. CronJob Missed Schedule
**Severity:** Warning
**Description:** CronJob is overdue by more than 5 minutes past its next scheduled execution time.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, cronjob,
  MAX(value) AS next_schedule_ts,
  1778940000 - MAX(value) AS seconds_overdue
FROM "kube_cronjob_next_schedule_time"
GROUP BY k8s_cluster, namespace, cronjob
HAVING seconds_overdue > 300
```

**PromQL Query:**
```promql
time() - kube_cronjob_next_schedule_time
```

**OpenObserve Stream:** `kube_cronjob_next_schedule_time`
**Threshold:** > 300
**Note:** Replace `1778940000` with the current Unix timestamp at alert evaluation time. The value stored is the next scheduled execution time in Unix seconds; `current_time - next_schedule_ts > 300` means the job is overdue by more than 5 minutes. In practice this alert is best implemented with PromQL where `time()` is dynamic.
**Status:** ✅ Created — alert name: `cronjob_missed_schedule`
**Action:** Check cluster resources and CronJob configuration

---

### 39. HorizontalPodAutoscaler Unable to Scale
**Severity:** Warning
**Description:** HPA is unable to scale the workload due to metric retrieval or configuration issues.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, horizontalpodautoscaler, condition, status,
  AVG(value) AS val
FROM "kube_horizontalpodautoscaler_status_condition"
WHERE condition = 'AbleToScale' AND status = 'false'
GROUP BY k8s_cluster, namespace, horizontalpodautoscaler, condition, status
HAVING val >= 1
```

**PromQL Query:**
```promql
kube_horizontalpodautoscaler_status_condition{condition='AbleToScale', status='false'}
```

**OpenObserve Stream:** `kube_horizontalpodautoscaler_status_condition`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `hpa_unable_to_scale`
**Action:** Check metrics server and HPA configuration

---

### 40. HorizontalPodAutoscaler At Max Replicas
**Severity:** Warning
**Description:** HPA has scaled to maximum replicas, workload may still be under pressure.

**SQL Query:**
```sql
SELECT curr.k8s_cluster, curr.namespace, curr.horizontalpodautoscaler,
  AVG(curr.value) AS current_replicas,
  AVG(maxr.value) AS max_replicas
FROM "kube_horizontalpodautoscaler_status_current_replicas" curr
JOIN "kube_horizontalpodautoscaler_spec_max_replicas" maxr
  ON curr.namespace = maxr.namespace
  AND curr.horizontalpodautoscaler = maxr.horizontalpodautoscaler
GROUP BY curr.k8s_cluster, curr.namespace, curr.horizontalpodautoscaler
HAVING current_replicas >= max_replicas
```

**PromQL Query:**
```promql
kube_horizontalpodautoscaler_status_current_replicas >= on(namespace, horizontalpodautoscaler, k8s_cluster) kube_horizontalpodautoscaler_spec_max_replicas
```

**OpenObserve Stream:** `kube_horizontalpodautoscaler_status_current_replicas`, `kube_horizontalpodautoscaler_spec_max_replicas`
**Threshold:** >= 1
**Status:** ✅ Created — alert name: `hpa_at_max_replicas`
**Action:** Review max replica limit and application load

---

## Control Plane Alerts

### 41. etcd High Request Latency
**Severity:** Critical
**Description:** etcd is experiencing high latency, impacting cluster state operations.

**SQL Query:** Not applicable — PromQL alert

**PromQL Query:** Not applicable — etcd metrics not available

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — etcd is managed by the cloud provider (AKS/EKS/GKE). etcd metrics are not exposed on managed Kubernetes clusters. This alert is only applicable to self-managed clusters.
**Action:** Check etcd disk I/O and cluster health

---

### 42. etcd Database Size Large
**Severity:** Warning
**Description:** etcd database size is approaching recommended limits.

**SQL Query:** Not applicable — PromQL alert

**PromQL Query:** Not applicable — etcd metrics not available

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — same reason as #41: etcd metrics are blocked on managed Kubernetes (AKS/EKS/GKE)
**Action:** Compact and defragment etcd database

---

### 43. Scheduler Binding Latency High
**Severity:** Warning
**Description:** Scheduler is taking longer than expected to bind pods to nodes.

**SQL Query:** Not applicable — PromQL alert

**PromQL Query:** Not applicable — scheduler metrics not available

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — scheduler metrics (port 10259) are blocked on managed Kubernetes (AKS/EKS/GKE) and are not accessible to the collector
**Action:** Investigate scheduler load and node availability

---

### 44. Controller Reconcile Errors
**Severity:** Warning
**Description:** Controller manager is experiencing reconciliation errors, indicating workload management issues.

**SQL Query:**
```sql
SELECT k8s_cluster, controller,
  (MAX(value) - MIN(value)) / 300.0 AS error_rate_per_sec
FROM "controller_runtime_reconcile_errors_total"
GROUP BY k8s_cluster, controller
HAVING error_rate_per_sec > 0.1
ORDER BY error_rate_per_sec DESC
```

**PromQL Query:**
```promql
floor(rate(controller_runtime_reconcile_errors_total[5m]) * 100) / 100
```

**OpenObserve Stream:** `controller_runtime_reconcile_errors_total`
**Threshold:** > 0.1
**Note:** `(MAX-MIN) / 300` approximates `rate()[5m]`. Adjust divisor to match your alert window in seconds.
**Status:** ✅ Created — alert name: `controller_reconcile_errors`
**Action:** Check controller manager logs and workload configurations

---

### 44b. Controller Workqueue Depth High
**Severity:** Warning
**Description:** Controller workqueue depth is high, indicating a backlog of reconciliation work.

**SQL Query:**
```sql
SELECT k8s_cluster, name,
  AVG(value) AS depth
FROM "workqueue_depth"
GROUP BY k8s_cluster, name
HAVING depth > 50
ORDER BY depth DESC
```

**PromQL Query:**
```promql
workqueue_depth
```

**OpenObserve Stream:** `workqueue_depth`
**Threshold:** > 50
**Status:** ✅ Created — alert name: `controller_workqueue_depth_high`
**Action:** Investigate controller throughput and API server health

---

### 45. Kubelet Down
**Severity:** Critical
**Description:** Kubelet on a node has stopped responding, making the node unschedulable and breaking pod lifecycle management.

**SQL Query:** Not applicable — covered by existing alert

**PromQL Query:** Not applicable — covered by Node Not Ready alert (#5)

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — covered by Node Not Ready (#5). When the kubelet stops responding, the node transitions to NotReady status within ~40 seconds, which is already caught by alert #5
**Action:** SSH to node and restart kubelet service

---

### 46. API Server Error Rate
**Severity:** Critical
**Description:** Kubernetes API server is returning 5xx errors at a rate exceeding 1 per second.

**SQL Query:**
```sql
SELECT k8s_cluster, verb, resource, code,
  (MAX(value) - MIN(value)) / 300.0 AS error_rate_per_sec
FROM "apiserver_request_total"
WHERE code LIKE '5%'
GROUP BY k8s_cluster, verb, resource, code
HAVING error_rate_per_sec > 1
ORDER BY error_rate_per_sec DESC
```

**PromQL Query:**
```promql
floor(sum by(k8s_cluster, verb, resource)(rate(apiserver_request_total{code=~'5..'}[5m])) * 100) / 100
```

**OpenObserve Stream:** `apiserver_request_total`
**Threshold:** > 1
**Note:** `code LIKE '5%'` matches all 5xx HTTP codes. `(MAX-MIN) / 300` approximates `rate()[5m]`.
**Status:** ✅ Created — alert name: `apiserver_error_rate_high`
**Action:** Emergency response — check control plane nodes and API server logs

---

### 46b. API Server Inflight Requests High
**Severity:** Warning
**Description:** Number of in-flight API server requests is high, risk of API server saturation.

**SQL Query:**
```sql
SELECT k8s_cluster, request_kind,
  AVG(value) AS inflight
FROM "apiserver_current_inflight_requests"
GROUP BY k8s_cluster, request_kind
HAVING inflight > 400
ORDER BY inflight DESC
```

**PromQL Query:**
```promql
apiserver_current_inflight_requests
```

**OpenObserve Stream:** `apiserver_current_inflight_requests`
**Threshold:** > 400
**Status:** ✅ Created — alert name: `apiserver_inflight_high`
**Action:** Review API server resource limits and identify high-frequency callers

---

### 46c. Admission Webhook Failures
**Severity:** Warning
**Description:** Admission webhooks are rejecting requests at a rate exceeding 0.5 per second.

**SQL Query:**
```sql
SELECT k8s_cluster, name, rejected,
  (MAX(value) - MIN(value)) / 300.0 AS rejection_rate_per_sec
FROM "apiserver_admission_webhook_request_total"
WHERE rejected = 'true'
GROUP BY k8s_cluster, name, rejected
HAVING rejection_rate_per_sec > 0.5
ORDER BY rejection_rate_per_sec DESC
```

**PromQL Query:**
```promql
floor(sum by(k8s_cluster, name)(rate(apiserver_admission_webhook_request_total{rejected='true'}[5m])) * 100) / 100
```

**OpenObserve Stream:** `apiserver_admission_webhook_request_total`
**Threshold:** > 0.5
**Status:** ✅ Created — alert name: `admission_webhook_failures`
**Action:** Check webhook endpoint health and configuration

---

### 47. Cloud Provider Rate Limiting
**Severity:** Warning
**Description:** Cloud provider API rate limiting is affecting cluster operations.

**SQL Query:** Not applicable — PromQL alert

**PromQL Query:** Not applicable — metric not available

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — `cloudprovider_*` metrics come from the controller-manager, which is blocked on managed Kubernetes (AKS/EKS/GKE)
**Action:** Review API usage and implement backoff strategies

---

## Security and Compliance Alerts

### 48. Privileged Container Running
**Severity:** Critical
**Description:** Container is running in privileged mode, potentially compromising cluster security.

**SQL Query:** Not applicable — PromQL alert

**PromQL Query:** Not applicable — metric removed from kube-state-metrics

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — `kube_pod_container_security_context_privileged` was removed in kube-state-metrics v2.x. Use Falco or OPA/Gatekeeper for runtime security enforcement instead
**Action:** Review security requirements and apply Pod Security Standards

---

### 49. Container Running as Root
**Severity:** Warning
**Description:** Container is running with root user (UID 0), violating security best practices.

**SQL Query:** Not applicable — PromQL alert

**PromQL Query:** Not applicable — metric removed from kube-state-metrics

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — `kube_pod_container_security_context_run_as_user` was removed in kube-state-metrics v2.x. Use Falco or OPA/Gatekeeper for runtime security enforcement instead
**Action:** Configure securityContext with non-root user

---

### 50. Pod Without Resource Limits
**Severity:** Warning
**Description:** Pod running without memory limits, risking resource exhaustion and noisy-neighbour issues.

**SQL Query:**
```sql
-- Find containers in kube_pod_container_info that have no memory limit entry
SELECT info.k8s_cluster, info.namespace, info.pod, info.container
FROM "kube_pod_container_info" info
WHERE NOT EXISTS (
  SELECT 1
  FROM "kube_pod_container_resource_limits" lim
  WHERE lim.namespace = info.namespace
    AND lim.pod = info.pod
    AND lim.container = info.container
    AND lim.resource = 'memory'
)
GROUP BY info.k8s_cluster, info.namespace, info.pod, info.container
LIMIT 100
```

**PromQL Query:**
```promql
kube_pod_container_info unless on(namespace, pod, container, k8s_cluster) kube_pod_container_resource_limits{resource='memory'}
```

**OpenObserve Stream:** `kube_pod_container_info`, `kube_pod_container_resource_limits`
**Threshold:** >= 1
**Frequency:** Every 30 minutes | **Silence:** 6 hours
**Note:** The `NOT EXISTS` subquery replicates the PromQL `unless` (set subtraction) operator. Results represent containers with no memory limit configured.
**Status:** ✅ Created — alert name: `pod_missing_resource_limits`
**Action:** Define resource limits for all containers

---

### 51. Unauthorized API Access Attempts
**Severity:** Critical
**Description:** Detected unauthorized access attempts to Kubernetes API at more than 10 per second.

**SQL Query:**
```sql
SELECT k8s_cluster, verb, resource, code,
  (MAX(value) - MIN(value)) / 300.0 AS auth_error_rate_per_sec
FROM "apiserver_request_total"
WHERE code IN ('401', '403')
GROUP BY k8s_cluster, verb, resource, code
HAVING auth_error_rate_per_sec > 10
ORDER BY auth_error_rate_per_sec DESC
```

**PromQL Query:**
```promql
floor(sum by(k8s_cluster, user)(rate(apiserver_request_total{code=~'401|403'}[5m])) * 100) / 100
```

**OpenObserve Stream:** `apiserver_request_total`
**Threshold:** > 10
**Note:** The `user` label is not available in `apiserver_request_total` in all collector configurations; the SQL groups by `verb` and `resource` instead. `(MAX-MIN) / 300` approximates `rate()[5m]`.
**Status:** ✅ Created — alert name: `unauthorized_api_access`
**Action:** Review RBAC policies and investigate potential security breach

---

### 52. Secret Accessed by Suspicious Pod
**Severity:** Warning
**Description:** Unusual pattern of secret access detected.

**SQL Query:** Not applicable — requires audit logs

**PromQL Query:** Not applicable — requires audit logs

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — secret access detection requires Kubernetes audit logs, which are not available as Prometheus metrics. Enable audit log shipping to OpenObserve to implement this alert
**Action:** Investigate pod behavior and verify legitimacy

---

### 53. Namespace Without Network Policy
**Severity:** Warning
**Description:** Active namespace has no NetworkPolicy defined, allowing unrestricted pod-to-pod communication.

**SQL Query:**
```sql
-- Find active namespaces that have no NetworkPolicy
SELECT ns.k8s_cluster, ns.namespace, ns.phase
FROM "kube_namespace_status_phase" ns
WHERE ns.phase = 'Active'
  AND ns.namespace NOT IN ('kube-system', 'kube-public', 'kube-node-lease')
  AND NOT EXISTS (
    SELECT 1
    FROM "kube_networkpolicy_created" np
    WHERE np.namespace = ns.namespace
  )
GROUP BY ns.k8s_cluster, ns.namespace, ns.phase
LIMIT 50
```

**PromQL Query:**
```promql
count by(namespace, k8s_cluster)(kube_namespace_status_phase{phase='Active', namespace!~'kube-system|kube-public|kube-node-lease'}) unless on(namespace, k8s_cluster) count by(namespace, k8s_cluster)(kube_networkpolicy_created)
```

**OpenObserve Stream:** `kube_namespace_status_phase`, `kube_networkpolicy_created`
**Threshold:** >= 1
**Frequency:** Every 60 minutes
**Note:** The `NOT EXISTS` subquery replicates the PromQL `unless` operator. Namespaces listed here have no NetworkPolicy at all.
**Status:** ✅ Created — alert name: `namespace_no_network_policy`
**Action:** Implement network segmentation with NetworkPolicy resources

---

### 54. Pod Security Policy Violation
**Severity:** Critical
**Description:** Pod violates defined Pod Security Standards or Policies.

**SQL Query:** Not applicable — PSP removed

**PromQL Query:** Not applicable — PSP removed

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — PodSecurityPolicy was removed in Kubernetes 1.25+. Use Pod Security Admission (PSA) or OPA/Gatekeeper for policy enforcement
**Action:** Update pod specifications to comply with security standards

---

### 55. Image Pull from Untrusted Registry
**Severity:** Warning
**Description:** Container image pulled from a registry not in the approved list.

**SQL Query:**
```sql
SELECT k8s_cluster, namespace, pod, container, image
FROM "kube_pod_container_info"
WHERE image NOT LIKE 'gcr.io/%'
  AND image NOT LIKE 'registry.k8s.io/%'
  AND image NOT LIKE 'docker.io/library/%'
  AND image NOT LIKE 'ghcr.io/%'
  AND image NOT LIKE 'quay.io/%'
  AND image NOT LIKE 'public.ecr.aws/%'
GROUP BY k8s_cluster, namespace, pod, container, image
LIMIT 50
```

**PromQL Query:**
```promql
kube_pod_container_info{image!~'(gcr.io|registry.k8s.io|docker.io/library|ghcr.io|quay.io|public.ecr.aws)/.*'}
```

**OpenObserve Stream:** `kube_pod_container_info`
**Threshold:** >= 1
**Note:** Customize the `NOT LIKE` clauses to match your organization's trusted registries before enabling this alert.
**Status:** ✅ Created — alert name: `image_untrusted_registry`
**Action:** Review and update image pull policies

---

### 56. ServiceAccount Token Exposure
**Severity:** Critical
**Description:** ServiceAccount token mounted in pod with elevated privileges.

**SQL Query:** Not applicable — requires audit logs

**PromQL Query:** Not applicable — requires audit logs

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — detecting privileged ServiceAccount token misuse requires Kubernetes audit logs, which are not available as Prometheus metrics
**Action:** Disable automatic token mounting for privileged service accounts

---

### 57. Admission Controller Webhook Failure
**Severity:** Critical
**Description:** Validating or mutating admission webhook is failing.

**SQL Query:** Not applicable — covered by alert 46c

**PromQL Query:** Not applicable — covered by alert 46c

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — see alert #46c (Admission Webhook Failures) which covers this use case with the verified `apiserver_admission_webhook_request_total` metric
**Action:** Check webhook endpoint health and configuration

---

## Resource Optimization Alerts

### 58. Over-Provisioned Container CPU
**Severity:** Info
**Description:** Container CPU utilization is below 10% of its request, indicating significant over-provisioning.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name,
  FLOOR(AVG(value) * 10000) / 100 AS cpu_request_pct
FROM "k8s_pod_cpu_request_utilization"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name
HAVING cpu_request_pct < 10 AND cpu_request_pct > 0
ORDER BY cpu_request_pct ASC
```

**PromQL Query:**
```promql
floor(k8s_pod_cpu_request_utilization * 10000) / 100
```

**OpenObserve Stream:** `k8s_pod_cpu_request_utilization`
**Threshold:** < 10
**Frequency:** Every 60 minutes | **Silence:** 24 hours
**Note:** `cpu_request_pct > 0` excludes idle/completed pods that report zero usage.
**Status:** ✅ Created — alert name: `container_cpu_over_provisioned`
**Action:** Right-size CPU requests to optimize cluster utilization

---

### 59. Over-Provisioned Container Memory
**Severity:** Info
**Description:** Container memory utilization is below 10% of its request, indicating significant over-provisioning.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name,
  FLOOR(AVG(value) * 10000) / 100 AS memory_request_pct
FROM "k8s_pod_memory_request_utilization"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name
HAVING memory_request_pct < 10 AND memory_request_pct > 0
ORDER BY memory_request_pct ASC
```

**PromQL Query:**
```promql
floor(k8s_pod_memory_request_utilization * 10000) / 100
```

**OpenObserve Stream:** `k8s_pod_memory_request_utilization`
**Threshold:** < 10
**Frequency:** Every 60 minutes | **Silence:** 24 hours
**Status:** ✅ Created — alert name: `container_memory_over_provisioned`
**Action:** Adjust memory requests based on actual usage patterns

---

### 60. Under-Provisioned Container Resources
**Severity:** Warning
**Description:** Container CPU utilization is at or above 95% of its request, risking throttling and performance issues.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name,
  FLOOR(AVG(value) * 10000) / 100 AS cpu_request_pct
FROM "k8s_pod_cpu_request_utilization"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name
HAVING cpu_request_pct >= 95
ORDER BY cpu_request_pct DESC
```

**PromQL Query:**
```promql
floor(k8s_pod_cpu_request_utilization * 10000) / 100
```

**OpenObserve Stream:** `k8s_pod_cpu_request_utilization`
**Threshold:** >= 95
**Frequency:** Every 30 minutes
**Status:** ✅ Created — alert name: `container_cpu_under_requested`
**Action:** Increase resource limits or scale horizontally

---

### 61. Empty or Low-Utilized Nodes
**Severity:** Info
**Description:** Node CPU utilization is below 10%, indicating a candidate for consolidation.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_node_name,
  FLOOR((1 - AVG(value)) * 10000) / 100 AS cpu_pct
FROM "system_cpu_utilization"
WHERE state = 'idle'
GROUP BY k8s_cluster, k8s_node_name
HAVING cpu_pct < 10
ORDER BY cpu_pct ASC
```

**PromQL Query:**
```promql
floor((1 - avg by(k8s_node_name, k8s_cluster)(system_cpu_utilization{state='idle'})) * 10000) / 100
```

**OpenObserve Stream:** `system_cpu_utilization`
**Threshold:** < 10
**Frequency:** Every 60 minutes | **Silence:** 24 hours
**Status:** ✅ Created — alert name: `node_low_utilization`
**Action:** Consider node consolidation to reduce infrastructure costs

---

### 62. Inefficient Storage Usage
**Severity:** Info
**Description:** PersistentVolume is provisioned but using less than 20% of its capacity.

**SQL Query:**
```sql
SELECT u.k8s_cluster, u.namespace, u.persistentvolumeclaim,
  FLOOR(AVG(u.value) / AVG(c.value) * 10000) / 100 AS pv_usage_pct
FROM "kubelet_volume_stats_used_bytes" u
JOIN "kubelet_volume_stats_capacity_bytes" c
  ON u.namespace = c.namespace
  AND u.persistentvolumeclaim = c.persistentvolumeclaim
GROUP BY u.k8s_cluster, u.namespace, u.persistentvolumeclaim
HAVING pv_usage_pct < 20 AND pv_usage_pct > 0
ORDER BY pv_usage_pct ASC
```

**PromQL Query:**
```promql
floor(kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 10000) / 100
```

**OpenObserve Stream:** `kubelet_volume_stats_used_bytes`
**Threshold:** < 20
**Frequency:** Every 60 minutes | **Silence:** 24 hours
**Note:** `pv_usage_pct > 0` excludes empty PVCs that may not have been mounted yet.
**Status:** ✅ Created — alert name: `storage_volume_under_utilized`
**Action:** Resize volumes or consolidate data

---

### 63. Pods Without Resource Requests
**Severity:** Warning
**Description:** Pods running without memory requests, affecting the scheduler's ability to make optimal placement decisions.

**SQL Query:**
```sql
SELECT info.k8s_cluster, info.namespace, info.pod, info.container
FROM "kube_pod_container_info" info
WHERE NOT EXISTS (
  SELECT 1
  FROM "kube_pod_container_resource_requests" req
  WHERE req.namespace = info.namespace
    AND req.pod = info.pod
    AND req.container = info.container
    AND req.resource = 'memory'
)
GROUP BY info.k8s_cluster, info.namespace, info.pod, info.container
LIMIT 100
```

**PromQL Query:**
```promql
kube_pod_container_info unless on(namespace, pod, container, k8s_cluster) kube_pod_container_resource_requests{resource='memory'}
```

**OpenObserve Stream:** `kube_pod_container_info`, `kube_pod_container_resource_requests`
**Threshold:** >= 1
**Frequency:** Every 30 minutes
**Note:** The `NOT EXISTS` subquery replicates the PromQL `unless` operator to find containers with no memory request configured.
**Status:** ✅ Created — alert name: `pod_missing_resource_requests`
**Action:** Define resource requests for predictable scheduling

---

## Application Performance Alerts

### 64. High Application Error Rate
**Severity:** Critical
**Description:** Application HTTP error rate (5xx) exceeds threshold.

**SQL Query:** Not applicable — requires app metrics

**PromQL Query:** Not applicable — requires app metrics

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — requires application-level HTTP metrics exposed via `prometheus.io/scrape` annotations. Not available from the cluster-level collector alone
**Action:** Instrument applications with Prometheus HTTP metrics and configure scraping

---

### 65. High Application Response Latency
**Severity:** Warning
**Description:** Application response time exceeds acceptable threshold.

**SQL Query:** Not applicable — requires app metrics

**PromQL Query:** Not applicable — requires app metrics

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — requires application-level latency histograms via `prometheus.io/scrape` annotations. Not available from the cluster-level collector alone
**Action:** Instrument applications with request duration histograms

---

### 66. Service Dependency Failure
**Severity:** Critical
**Description:** Upstream service dependency experiencing failures.

**SQL Query:** Not applicable — requires service mesh

**PromQL Query:** Not applicable — requires service mesh

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — requires a service mesh (Istio/Linkerd) to expose inter-service traffic metrics
**Action:** Deploy a service mesh and configure inter-service monitoring

---

### 67. Slow Database Queries
**Severity:** Warning
**Description:** Database query performance degradation detected.

**SQL Query:** Not applicable — requires database exporter

**PromQL Query:** Not applicable — requires database exporter

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — requires a database-specific exporter (e.g., postgres_exporter, mysqld_exporter)
**Action:** Deploy a database exporter and configure slow query monitoring

---

### 68. Request Queue Buildup
**Severity:** Warning
**Description:** Kubernetes controller workqueue P99 queue duration exceeds 1 second, indicating processing delays.

**SQL Query:**
```sql
-- Approximate: growth in requests completing within 1s bucket (le='1')
-- Low growth here indicates many requests taking >1s (high P99 latency)
SELECT k8s_cluster, name,
  MAX(value) - MIN(value) AS requests_under_1s
FROM "workqueue_queue_duration_seconds_bucket"
WHERE le = '1'
GROUP BY k8s_cluster, name
ORDER BY requests_under_1s ASC
LIMIT 20
```

**PromQL Query:**
```promql
floor(histogram_quantile(0.99, sum by(k8s_cluster, name, le)(rate(workqueue_queue_duration_seconds_bucket[5m]))) * 1000) / 1
```

**OpenObserve Stream:** `workqueue_queue_duration_seconds_bucket`
**Threshold:** > 1000 (milliseconds)
**Note:** True `histogram_quantile` is not possible in SQL. The SQL monitors bucket growth in the `le='1'` (1-second) bucket as a proxy; low growth relative to total activity indicates the P99 exceeds 1s. Use the PromQL alert for precision.
**Status:** ✅ Created — alert name: `workqueue_queue_duration_high`
**Action:** Scale application or optimize processing logic

---

### 69. Cache Miss Rate High
**Severity:** Warning
**Description:** Application cache effectiveness degraded.

**SQL Query:** Not applicable — requires app cache metrics

**PromQL Query:** Not applicable — requires app cache metrics

**OpenObserve Stream:** N/A
**Threshold:** N/A
**Status:** ⛔ Skipped — requires application-level cache metrics. Not available from the cluster-level collector
**Action:** Instrument applications with cache hit/miss counters

---

### 70. High GC Pressure (Go)
**Severity:** Warning
**Description:** Go garbage collection average pause time exceeds 100ms.

**SQL Query:**
```sql
SELECT s.k8s_cluster, s.k8s_namespace_name, s.k8s_pod_name,
  FLOOR(
    (MAX(s.value) - MIN(s.value)) /
    NULLIF(MAX(c.value) - MIN(c.value), 0)
    * 1000
  ) AS avg_gc_pause_ms
FROM "go_gc_duration_seconds_sum" s
JOIN "go_gc_duration_seconds_count" c
  ON s.k8s_namespace_name = c.k8s_namespace_name
  AND s.k8s_pod_name = c.k8s_pod_name
GROUP BY s.k8s_cluster, s.k8s_namespace_name, s.k8s_pod_name
HAVING avg_gc_pause_ms > 100
ORDER BY avg_gc_pause_ms DESC
```

**PromQL Query:**
```promql
floor(rate(go_gc_duration_seconds_sum[5m]) / rate(go_gc_duration_seconds_count[5m]) * 1000) / 1
```

**OpenObserve Stream:** `go_gc_duration_seconds_sum`, `go_gc_duration_seconds_count`
**Threshold:** > 100 (milliseconds)
**Note:** `(MAX-MIN)` approximates `rate()` increase over the window. `NULLIF(..., 0)` prevents division by zero when GC count did not increase (no GC cycles during window).
**Status:** ✅ Created — alert name: `go_gc_pause_high`
**Action:** Tune heap size or investigate memory leaks

---

### 70b. High GC Rate (Go)
**Severity:** Warning
**Description:** Go garbage collection is running at more than 10 collections per minute.

**SQL Query:**
```sql
SELECT k8s_cluster, k8s_namespace_name, k8s_pod_name,
  FLOOR((MAX(value) - MIN(value)) / 300.0 * 60 * 100) / 100 AS gc_per_minute
FROM "go_gc_duration_seconds_count"
GROUP BY k8s_cluster, k8s_namespace_name, k8s_pod_name
HAVING gc_per_minute > 10
ORDER BY gc_per_minute DESC
```

**PromQL Query:**
```promql
floor(rate(go_gc_duration_seconds_count[5m]) * 60 * 100) / 100
```

**OpenObserve Stream:** `go_gc_duration_seconds_count`
**Threshold:** > 10 (collections per minute)
**Note:** `(MAX-MIN) / 300 * 60` converts the 5-minute counter increase to a per-minute rate. Adjust `300` to match your alert window in seconds.
**Status:** ✅ Created — alert name: `go_gc_rate_high`
**Action:** Tune heap size or investigate memory allocation patterns

---

## Kubernetes Events Alerts

> These alerts are SQL-based and query the `k8s_events` log stream collected by the OpenObserve collector's Kubernetes events receiver.
>
> **Field mapping:** `body_object_reason` (event reason), `body_object_type` (Warning/Normal), `body_object_note` (event message), `k8s_namespace_name`, `k8s_cluster`, `event_name`

### 71. Pod Scheduling Failures
**Severity:** Warning
**Description:** Kubernetes events indicate repeated pod scheduling failures in a namespace.

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'FailedScheduling')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 5
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 5 in the query window (5 minutes)
**Status:** ✅ Created — alert name: `pod_scheduling_failures_events`
**Action:** Review resource requests and cluster capacity

---

### 72. Image Pull Errors (Events)
**Severity:** Warning
**Description:** Multiple image pull failure events detected in a namespace within 10 minutes.

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND (
    str_match(body_object_reason, 'BackOff')
    OR str_match(body_object_reason, 'ErrImagePull')
    OR str_match(body_object_reason, 'Failed')
  )
  AND str_match(body_object_note, 'image')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 3
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 3 in the query window (10 minutes)
**Status:** ✅ Created — alert name: `image_pull_errors_events`
**Action:** Verify image registry accessibility and credentials

---

### 73. Volume Mount Failures
**Severity:** Critical
**Description:** Persistent volume mounting failure events detected — any occurrence warrants immediate investigation.

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND (
    str_match(body_object_reason, 'FailedMount')
    OR str_match(body_object_reason, 'FailedAttachVolume')
    OR str_match(body_object_reason, 'VolumeFailedAttach')
  )
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 (any occurrence)
**Status:** ✅ Created — alert name: `volume_mount_failures_events`
**Action:** Check PVC binding and storage backend health

---

### 74. Node Condition Change Events
**Severity:** Warning
**Description:** Node condition warning events (NotReady, DiskPressure, MemoryPressure) have been detected.

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, event_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND (
    str_match(body_object_reason, 'NodeNotReady')
    OR str_match(body_object_reason, 'NodeHasDiskPressure')
    OR str_match(body_object_reason, 'NodeHasMemoryPressure')
  )
GROUP BY k8s_cluster, event_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 (any occurrence)
**Status:** ✅ Created — alert name: `node_condition_change_events`
**Action:** Investigate node health and kubelet logs

---

### 75. High Warning Event Rate
**Severity:** Warning
**Description:** Unusually high rate of Kubernetes Warning events across the cluster in 5 minutes — may indicate a cascading failure.

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
GROUP BY k8s_cluster
HAVING event_count > 100
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 100 in the query window (5 minutes)
**Status:** ✅ Created — alert name: `high_warning_event_rate`
**Action:** Identify event source and investigate underlying issue

---

### 76. OOM Killing Events
**Severity:** Critical
**Description:** The Linux kernel OOM killer is actively terminating processes on a node due to memory exhaustion. This is distinct from `pod_oom_killed` (which tracks pod status) — this fires when the kernel itself is killing processes.
**Validated:** o2aks1: 2,025 events, us2cloud: 28 events

> ⚠️ **Important:** `OOMKilling` is a **node-level event** — `body_object_regarding.kind = Node`. The `k8s_namespace_name` field is always `default` (the namespace of the Event object itself, not the pod). Group by `event_name` to get the actual node name.

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, event_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'OOMKilling')
GROUP BY k8s_cluster, event_name
HAVING event_count > 0
```

**Sample event note:** `Memory cgroup out of memory: Killed process 1617000 (openobserve) total-vm:18545720kB, anon-rss:8112432kB`

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 per node (2-min window)
**Status:** ✅ Created — alert name: `oom_killing_events`
**Action:** The `body_object_note` field in the raw event contains the process name and memory stats. Run: `SELECT body_object_note, event_name FROM "k8s_events" WHERE str_match(body_object_reason, 'OOMKilling')` to identify exactly what was killed. Then check pods on that node and increase memory limits.

---

### 77. Pod Unhealthy Probe Events
**Severity:** Warning
**Description:** Pods are repeatedly failing readiness or liveness probes, generating Unhealthy events. A high rate suggests application health issues or misconfigured probes.
**Validated:** o2aks1/devcluster2: 518, introspection/openobserve: 146, quadrantsec/ingress-nginx: 113

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'Unhealthy')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 10
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 10 in 5 minutes
**Status:** ✅ Created — alert name: `pod_unhealthy_probe_events`
**Action:** Check application health endpoints. Review probe configuration (path, port, timeouts). Inspect pod logs.

---

### 78. CoreDNS Unreachable Events
**Severity:** Critical
**Description:** CoreDNS is unreachable from nodes, causing complete in-cluster DNS resolution failure. All service discovery and inter-pod communication by hostname is broken.
**Validated:** o2aks1: 516 events

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'CoreDNSUnreachable')
GROUP BY k8s_cluster
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 (any occurrence, 2-min window)
**Status:** ✅ Created — alert name: `coredns_unreachable_events`
**Action:** Check CoreDNS pod status. Verify kube-dns Service exists. Restart CoreDNS pods if needed.

---

### 79. Node Shutdown Events
**Severity:** Critical
**Description:** A node is shutting down, causing all pods to be evicted. Can indicate hardware failure, cloud provider instance termination, or unexpected OS shutdown.
**Validated:** introspection: collector and node-exporter nodes detected

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, event_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'NodeShutdown')
GROUP BY k8s_cluster, event_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 (any occurrence, 2-min window)
**Status:** ✅ Created — alert name: `node_shutdown_events`
**Action:** Investigate node in cloud console. Check if planned (maintenance) or unplanned. Verify workloads rescheduled on healthy nodes.

---

### 80. Job Backoff Limit Exceeded Events
**Severity:** Warning
**Description:** A Kubernetes Job has failed all retry attempts and will not be retried. The job is permanently failed.
**Validated:** o2aks1/trivy-system: 761 (Trivy security scanner jobs failing repeatedly)

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'BackoffLimitExceeded')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 in 5 minutes
**Status:** ✅ Created — alert name: `job_backoff_limit_exceeded_events`
**Action:** Check job logs for root cause. Fix application error or increase backoffLimit if transient failures expected.

---

### 81. Image Pull Secret Missing Events
**Severity:** Warning
**Description:** Pods cannot retrieve the image pull secret, preventing container images from being pulled. Usually indicates a missing or incorrectly named secret in the namespace.
**Validated:** production/license-validator: 344, production/casdoor: 321

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'FailedToRetrieveImagePullSecret')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 in 5 minutes
**Status:** ✅ Created — alert name: `image_pull_secret_missing_events`
**Action:** Verify secret exists in the namespace. Check secret name matches `imagePullSecrets` in pod spec. Recreate secret if expired.

---

### 82. HPA Metric Unavailable Events
**Severity:** Warning
**Description:** Horizontal Pod Autoscaler cannot retrieve resource metrics, making it unable to make accurate scaling decisions. HPA is effectively blind.
**Validated:** quadrantsec/openobserve: 346 events — HPA scaling is currently blind in this cluster

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'FailedGetResourceMetric')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 3
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 3 in 5 minutes
**Status:** ✅ Created — alert name: `hpa_metric_unavailable_events`
**Action:** Check metrics-server is running. Verify pods have resource requests set. Check HPA target reference is correct.

---

### 83. Node Drain Failed Events
**Severity:** Warning
**Description:** Node drain operation is failing, blocking cluster upgrades, maintenance, or node replacement. Usually caused by PodDisruptionBudgets or pods without owners.
**Validated:** o2aks1 and common-dev nodes: drain failures detected

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, event_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'FailedDraining')
GROUP BY k8s_cluster, event_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 in 5 minutes
**Status:** ✅ Created — alert name: `node_drain_failed_events`
**Action:** Check PodDisruptionBudgets blocking eviction. Identify pods preventing drain. Use `kubectl drain --force --ignore-daemonsets` if safe.

---

### 84. Pod Sandbox Creation Failed Events
**Severity:** Warning
**Description:** Pod network sandbox (pause container) cannot be created, preventing pod networking from initializing. Typically caused by CNI plugin failures or container runtime issues.
**Validated:** o2aks1/openobserve-collector: 91 events

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'FailedCreatePodSandBox')
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 3
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 3 in 5 minutes
**Status:** ✅ Created — alert name: `pod_sandbox_failed_events`
**Action:** Check CNI DaemonSet pods. Restart container runtime on affected node. Review CNI plugin logs.

---

### 85. Network Not Ready Events
**Severity:** Warning
**Description:** CNI network plugin is not ready on a node, preventing new pods from being scheduled with networking. Existing pods may lose connectivity.
**Validated:** common-dev and introspection: 6 events each on ebs-csi-node and collector pods

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, event_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND str_match(body_object_reason, 'NetworkNotReady')
GROUP BY k8s_cluster, event_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 in 2 minutes
**Status:** ✅ Created — alert name: `network_not_ready_events`
**Action:** Check CNI DaemonSet on the affected node. Verify network plugin configuration. Restart kubelet or node if persistent.

---

### 86. Azure Scheduled Maintenance Events (AKS)
**Severity:** Warning
**Description:** Azure is scheduling VM maintenance on AKS nodes (Freeze, Preempt, Terminate, or Redeploy). This is a **pre-warning** — the node will be unavailable soon. Plan workload disruption accordingly.
**Validated:** o2aks1 FreezeScheduled: 16 events, PreemptScheduled: 4 events (spot node preemption); us2cloud FreezeScheduled: 16 events

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, event_name, body_object_reason
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND (
    str_match(body_object_reason, 'FreezeScheduled')
    OR str_match(body_object_reason, 'PreemptScheduled')
    OR str_match(body_object_reason, 'TerminateScheduled')
    OR str_match(body_object_reason, 'RedeployScheduled')
  )
GROUP BY k8s_cluster, event_name, body_object_reason
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 in 5 minutes (2h silence to avoid repeat)
**Status:** ✅ Created — alert name: `azure_maintenance_scheduled_events`
**Action:** Review upcoming maintenance window. Ensure PodDisruptionBudgets allow disruption. For spot nodes (PreemptScheduled), verify workloads tolerate preemption.

---

### 87. Azure Storage Provisioning Failed Events (AKS)
**Severity:** Warning
**Description:** Azure disk/storage provisioning is failing, leaving PVCs in Pending state. Can be caused by Azure quota limits, region capacity, or disk SKU unavailability.
**Validated:** o2aks1/default: 97 events, common-dev/alert-test: 14 events

**SQL Query:**
```sql
SELECT count(*) as event_count, k8s_cluster, k8s_namespace_name
FROM "k8s_events"
WHERE k8s_resource_name = 'events'
  AND body_object_type = 'Warning'
  AND (
    str_match(body_object_reason, 'AsyncProvisioningError')
    OR str_match(body_object_reason, 'ProvisioningFailed')
    OR str_match(body_object_reason, 'VolumeFailedDelete')
  )
GROUP BY k8s_cluster, k8s_namespace_name
HAVING event_count > 0
```

**PromQL Query:** Not applicable — SQL/events-based alert
**OpenObserve Stream:** `k8s_events` (log stream)
**Threshold:** event_count > 0 in 5 minutes
**Status:** ✅ Created — alert name: `azure_storage_provisioning_failed_events`
**Action:** Check Azure subscription disk quota. Verify StorageClass configuration. Review Azure portal for regional capacity issues.

---

## Alert Implementation Notes

### Severity Levels

- **Critical:** Immediate action required, service impact likely
- **Warning:** Investigation needed, potential service impact
- **Info:** Informational, useful for tracking trends

### Best Practices

1. **Tune Thresholds:** Adjust thresholds based on your workload patterns
2. **Reduce Noise:** Use appropriate time windows to avoid alert fatigue
3. **Group Alerts:** Correlate related alerts to identify root causes
4. **Test Alerts:** Validate alerts in non-production environments first
5. **Document Actions:** Maintain runbooks for each alert type
6. **Review Regularly:** Periodically review alert effectiveness and adjust

### Integration with OpenObserve

All alerts can be configured in OpenObserve using:
- Alert rules based on the provided queries
- Notification channels (Slack, PagerDuty, email, webhooks)
- Alert grouping and silencing policies
- Custom dashboards for alert visualization

### Label Conventions

| Receiver | Label style | Example labels |
|---|---|---|
| kube-state-metrics | Short labels | `node`, `pod`, `namespace`, `container` |
| kubeletstats / hostmetrics | Prefixed labels | `k8s_node_name`, `k8s_pod_name`, `k8s_namespace_name` |
| All alerts | Cluster label | `k8s_cluster` |

### SQL Query Conventions

| Pattern | Usage | Example |
|---|---|---|
| `AVG(value)` | Gauge metrics (current state) | CPU %, memory % |
| `MAX(value) - MIN(value)` | Counter increase over window | Restart count, error increase |
| `(MAX(value) - MIN(value)) / 300.0` | Rate per second (5-min window) | Error rate/sec, network errors/sec |
| `FLOOR(expr * 10000) / 100` | 2 decimal place percentage | CPU%, memory% |
| `JOIN ... ON stream_a.field = stream_b.field` | Cross-stream ratio | Disk usage%, PV usage% |
| `NOT EXISTS (SELECT 1 FROM ...)` | Set subtraction (PromQL `unless`) | Missing limits/requests |
| `NULLIF(expr, 0)` | Safe division | GC avg pause time |

### Decimal Formatting Convention

All percentage values use `floor(expr * 10000) / 100` to produce 2 decimal places. `round()` is used only for integer counts (e.g., restart counts from `increase()`).

### Histogram Alerts (SQL Limitation)

The following alerts use `histogram_quantile` in PromQL, which cannot be exactly replicated in SQL. For these alerts, SQL provides a proxy approximation; use the PromQL version for precise threshold enforcement:

- **#25** API Server High Latency — monitors `apiserver_request_duration_seconds_bucket`
- **#33** DNS High Latency — monitors `coredns_dns_request_duration_seconds_bucket`
- **#68** Request Queue Buildup — monitors `workqueue_queue_duration_seconds_bucket`

### Maintenance

- Review alert performance monthly
- Update thresholds based on seasonal patterns
- Archive or remove alerts that consistently false-positive
- Add new alerts as infrastructure evolves

---

## Quick Start Checklist

Essential alerts to configure first for immediate cluster protection:

### Critical Infrastructure (Priority 1)
- [ ] Node Not Ready (#5)
- [ ] OOM Killing Events (#76) — kernel killing processes
- [ ] CoreDNS Unreachable (#78) — all DNS broken
- [ ] Node Shutdown Events (#79)
- [ ] API Server Error Rate (#46)
- [ ] Controller Reconcile Errors (#44)
- [ ] Volume Mount Failures (#73)

### Pod Health (Priority 2)
- [ ] Pod CrashLoopBackOff (#10)
- [ ] Pod OOMKilled (#15)
- [ ] Pod Failed State (#13)
- [ ] High Pod Restart Rate (#11)

### Resource Management (Priority 3)
- [ ] Critical Node CPU Usage (#2)
- [ ] Critical Node Memory Usage (#4)
- [ ] Container Memory Near Limit (#18)
- [ ] Container CPU Near Limit (#17)

### Workload Health (Priority 4)
- [ ] Deployment Replica Mismatch (#34)
- [ ] StatefulSet Replica Mismatch (#35)
- [ ] DaemonSet Missing Pods (#36)
- [ ] HPA Unable to Scale (#39)

### Network & Storage (Priority 5)
- [ ] Service No Ready Endpoints (#31)
- [ ] PVC Pending (#27)
- [ ] PV Failed (#26)
- [ ] DNS Resolution Failures (#32)

### Security (Priority 6)
- [ ] Unauthorized API Access (#51)
- [ ] Namespace Without Network Policy (#53)
- [ ] Image From Untrusted Registry (#55)
- [ ] Admission Webhook Failures (#46c)

### Application Performance (Priority 7)
- [ ] Request Queue Buildup (#68)
- [ ] Go GC Pause High (#70)
- [ ] API Server High Latency (#25)

### AKS / Cloud-Specific (Priority 8)
- [ ] Azure Maintenance Scheduled (#86) — pre-warning before node freeze/preemption
- [ ] Azure Storage Provisioning Failed (#87)
- [ ] Image Pull Secret Missing (#81)
- [ ] HPA Metric Unavailable (#82) — scaling is blind
- [ ] Node Drain Failed (#83) — upgrade/maintenance blocked

Start with Priority 1-3 alerts for essential cluster stability, then gradually add others based on your operational needs and maturity.

---

## Alert Summary

**Total Alerts in OpenObserve (folder: mdmosaraf):** 76 created

**By Category (actual):**
| Category | Created | Alert Names |
|----------|---------|-------------|
| Node-Level | 10 | node_high_cpu_utilization, node_critical_cpu_utilization, node_high_memory_usage, node_critical_memory_usage, node_high_disk_usage, node_critical_disk_usage, node_disk_pressure, node_memory_pressure, node_not_ready, node_unschedulable |
| Pod-Level | 7 | pod_crashloop_backoff, pod_high_restart_rate, pod_pending_too_long, pod_failed_state, pod_image_pull_backoff, pod_oom_killed, pod_evicted |
| Container-Level | 4 | container_cpu_limit_high, container_memory_near_limit, container_not_ready, container_restarted |
| Cluster-Level | 5 | cluster_cpu_capacity_high, cluster_memory_capacity_high, cluster_pod_count_high, apiserver_high_latency, certificate_expiry_warning |
| Storage | 4 | pv_failed, pvc_pending, pvc_lost, pv_usage_high |
| Network | 4 | node_network_errors_high, service_no_ready_endpoints, dns_resolution_failures_high, dns_high_latency |
| Workload Health | 7 | deployment_replica_mismatch, statefulset_replica_mismatch, daemonset_pods_not_scheduled, job_failed, cronjob_missed_schedule, hpa_unable_to_scale, hpa_at_max_replicas |
| Control Plane | 5 | controller_reconcile_errors_high, controller_workqueue_depth_high, apiserver_error_rate_high, apiserver_inflight_requests_high, admission_webhook_failures_high |
| Security | 4 | pod_missing_resource_limits, unauthorized_api_access_high, image_from_untrusted_registry, namespace_without_network_policy |
| Resource Optimization | 6 | container_cpu_over_provisioned, container_memory_over_provisioned, container_resource_under_requested, node_low_utilization, storage_volume_under_utilized, pods_without_resource_requests |
| App Performance | 3 | go_gc_pause_high, go_gc_rate_high, controller_queue_processing_slow |
| K8s Events (SQL) — Original | 5 | pod_scheduling_failures_events, image_pull_errors_events, volume_mount_failures_events, node_condition_change_events, high_warning_event_rate |
| K8s Events (SQL) — Extended | 12 | oom_killing_events, pod_unhealthy_probe_events, coredns_unreachable_events, node_shutdown_events, job_backoff_limit_exceeded_events, image_pull_secret_missing_events, hpa_metric_unavailable_events, node_drain_failed_events, pod_sandbox_failed_events, network_not_ready_events, azure_maintenance_scheduled_events, azure_storage_provisioning_failed_events |
| **TOTAL** | **76** | |

**Skipped Alerts (not creatable from collector data):**
- `#41, #42` etcd latency/size — etcd managed by cloud provider (AKS/EKS/GKE), endpoint not exposed
- `#43` scheduler latency — port :10259 blocked on managed K8s
- `#47` cloudprovider rate limiting — controller-manager blocked on managed K8s
- `#48` privileged container — `kube_pod_container_security_context_privileged` removed in kube-state-metrics v2.x (use Falco)
- `#49` container running as root — same as above
- `#52` secret access — requires K8s audit logs, not Prometheus metrics
- `#54` PSP violation — PodSecurityPolicy removed in K8s 1.25+
- `#56` ServiceAccount token exposure — requires audit logs
- `#29` StorageClass provisioning — `storage_operation_duration_seconds_count` not collected
- `#64, #65` HTTP error rate / latency — requires app `prometheus.io/scrape` instrumentation
- `#66` service dependency failure — requires Istio/Linkerd service mesh
- `#67` slow DB queries — requires database exporter
- `#69` cache miss rate — requires app-level cache metrics
