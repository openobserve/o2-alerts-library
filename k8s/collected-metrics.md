# OpenObserve Collector — Metrics Reference

Source: https://github.com/openobserve/openobserve-helm-chart/tree/main/charts/openobserve-collector

OpenTelemetry metric names use dots (`.`) which OpenObserve stores with underscores (`_`).
e.g. `k8s.node.cpu.usage` → `k8s_node_cpu_usage`

---

## Architecture

| Component | Type | Runs On | Purpose |
|-----------|------|---------|---------|
| **Agent** | DaemonSet | Every node | Container logs + host metrics + kubelet stats |
| **Gateway** | Deployment | Cluster-wide | K8s object events + Prometheus scraping |

---

## Agent Metrics (per node via DaemonSet)

### 1. Host Metrics (`hostmetricsreceiver`)

Collected every **30s** from host filesystem (`/hostfs`).

#### CPU
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `system_cpu_utilization` | `state` (user, system, idle, iowait, steal, irq, softirq), `cpu`, `k8s_node_name`, `k8s_cluster` | CPU utilization ratio (0–1) per state per CPU core |
| `system_cpu_time` | `state`, `cpu`, `k8s_node_name`, `k8s_cluster` | CPU time in seconds |
| `system_cpu_load_average_1m` | `k8s_node_name`, `k8s_cluster` | 1-minute load average |
| `system_cpu_load_average_5m` | `k8s_node_name`, `k8s_cluster` | 5-minute load average |
| `system_cpu_load_average_15m` | `k8s_node_name`, `k8s_cluster` | 15-minute load average |

**Alert PromQL for CPU utilization:**
```promql
1 - avg by (k8s_node_name, k8s_cluster) (system_cpu_utilization{state="idle"})
```

#### Memory
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `system_memory_utilization` | `state` (used, free, buffered, cached, slab_reclaimable, slab_unreclaimable), `k8s_node_name`, `k8s_cluster` | Memory utilization ratio (0–1) per state |
| `system_memory_usage` | `state`, `k8s_node_name`, `k8s_cluster` | Memory usage in bytes |

**Alert PromQL for memory utilization:**
```promql
system_memory_utilization{state="used"}
```

#### Filesystem
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `system_filesystem_usage` | `device`, `mountpoint`, `type`, `state` (used, free, reserved), `k8s_node_name`, `k8s_cluster` | Filesystem usage in bytes |
| `system_filesystem_inodes_usage` | `device`, `mountpoint`, `type`, `state`, `k8s_node_name`, `k8s_cluster` | Inode usage |

> ⚠️ `system_filesystem_utilization` is NOT collected. Use `k8s_node_filesystem_usage / k8s_node_filesystem_capacity` from kubeletstats instead.

**Alert PromQL for disk utilization:**
```promql
k8s_node_filesystem_usage / k8s_node_filesystem_capacity
```

#### Network
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `system_network_io` | `device`, `direction` (transmit, receive), `k8s_node_name`, `k8s_cluster` | Network bytes transmitted/received |
| `system_network_errors` | `device`, `direction`, `k8s_node_name`, `k8s_cluster` | Network error count |
| `system_network_dropped` | `device`, `direction`, `k8s_node_name`, `k8s_cluster` | Dropped packets count |
| `system_network_packets` | `device`, `direction`, `k8s_node_name`, `k8s_cluster` | Packet count |

#### Disk I/O
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `system_disk_io` | `device`, `direction` (read, write), `k8s_node_name`, `k8s_cluster` | Disk bytes read/written |
| `system_disk_operations` | `device`, `direction`, `k8s_node_name`, `k8s_cluster` | Disk operation count |
| `system_disk_io_time` | `device`, `k8s_node_name`, `k8s_cluster` | Time disk spent busy |

#### Processes
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `system_processes_count` | `status` (running, sleeping, stopped, zombie), `k8s_node_name`, `k8s_cluster` | Process count by state |
| `system_processes_created` | `k8s_node_name`, `k8s_cluster` | Processes created total |

---

### 2. Kubelet Stats (`kubeletstatsreceiver`)

Collected every **30s** via kubelet API (per node). Covers node, pod, container, and volume groups.

#### Node Metrics
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `k8s_node_cpu_usage` | `k8s_node_name`, `k8s_cluster` | CPU usage in cores (raw) |
| `k8s_node_cpu_time` | `k8s_node_name`, `k8s_cluster` | Cumulative CPU time |
| `k8s_node_memory_usage` | `k8s_node_name`, `k8s_cluster` | Memory usage in bytes |
| `k8s_node_memory_available` | `k8s_node_name`, `k8s_cluster` | Available memory in bytes |
| `k8s_node_memory_working_set` | `k8s_node_name`, `k8s_cluster` | Working set memory in bytes |
| `k8s_node_memory_rss` | `k8s_node_name`, `k8s_cluster` | RSS memory in bytes |
| `k8s_node_memory_page_faults` | `k8s_node_name`, `k8s_cluster` | Page faults count |
| `k8s_node_memory_major_page_faults` | `k8s_node_name`, `k8s_cluster` | Major page faults count |
| `k8s_node_filesystem_usage` | `k8s_node_name`, `k8s_cluster` | Node filesystem bytes used |
| `k8s_node_filesystem_available` | `k8s_node_name`, `k8s_cluster` | Node filesystem bytes available |
| `k8s_node_filesystem_capacity` | `k8s_node_name`, `k8s_cluster` | Node filesystem total capacity |
| `k8s_node_network_io` | `k8s_node_name`, `k8s_cluster`, `direction`, `interface` | Node network bytes |
| `k8s_node_network_errors` | `k8s_node_name`, `k8s_cluster`, `direction`, `interface` | Node network errors |

#### Pod Metrics
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `k8s_pod_cpu_usage` | `k8s_pod_name`, `k8s_namespace_name`, `k8s_node_name`, `k8s_cluster` | Pod CPU usage in cores |
| `k8s_pod_cpu_limit_utilization` | same + `k8s_deployment_name` | CPU usage as fraction of limit (0–1) |
| `k8s_pod_cpu_request_utilization` | same | CPU usage as fraction of request (0–1) |
| `k8s_pod_memory_usage` | `k8s_pod_name`, `k8s_namespace_name`, `k8s_node_name`, `k8s_cluster` | Pod memory usage in bytes |
| `k8s_pod_memory_available` | same | Available memory in bytes |
| `k8s_pod_memory_working_set` | same | Working set memory |
| `k8s_pod_memory_rss` | same | RSS memory |
| `k8s_pod_memory_limit_utilization` | same | Memory usage as fraction of limit (0–1) |
| `k8s_pod_memory_request_utilization` | same | Memory usage as fraction of request (0–1) |
| `k8s_pod_filesystem_usage` | same + `k8s_volume_type` | Pod filesystem usage |
| `k8s_pod_filesystem_available` | same | Pod filesystem available |
| `k8s_pod_filesystem_capacity` | same | Pod filesystem capacity |
| `k8s_pod_network_io` | same + `direction`, `interface` | Pod network bytes |
| `k8s_pod_network_errors` | same + `direction`, `interface` | Pod network errors |
| `k8s_pod_phase` | `k8s_pod_name`, `k8s_namespace_name`, `k8s_node_name`, `k8s_cluster`, `phase` (Running/Pending/Failed/Succeeded/Unknown) | Pod phase (value=1 for current phase) |

#### Container Metrics
| OpenObserve Metric | Labels | Description |
|--------------------|--------|-------------|
| `k8s_container_cpu_usage` | `k8s_container_name`, `k8s_pod_name`, `k8s_namespace_name`, `k8s_node_name`, `k8s_cluster` | Container CPU usage in cores |
| `k8s_container_memory_usage` | same | Container memory usage |
| `k8s_container_memory_working_set` | same | Container working set |
| `k8s_container_memory_rss` | same | Container RSS memory |
| `k8s_container_restarts` | same | Container restart count (cumulative) |
| `k8s_container_ready` | same | Container ready (1=ready, 0=not ready) |

---

## Gateway Metrics (Cluster-wide via Deployment)

### 3. Kubernetes Object Events (Logs stream: `k8s_events`)

Collected as **logs** via `k8sobjects` receiver in watch mode. All changes are captured as log events.

| Object Type | Stream | Key Fields |
|-------------|--------|------------|
| Events | `k8s_events` | `reason`, `message`, `type` (Normal/Warning), `involvedObject.kind/name/namespace` |
| Pods | `k8s_events` | `phase`, `conditions`, `containerStatuses` |
| Nodes | `k8s_events` | `conditions`, `allocatable`, `capacity` |
| Deployments | `k8s_events` | `replicas`, `readyReplicas`, `availableReplicas` |
| DaemonSets | `k8s_events` | `desiredNumberScheduled`, `numberReady` |
| StatefulSets | `k8s_events` | `replicas`, `readyReplicas` |
| Services | `k8s_events` | `type`, `clusterIP`, `loadBalancer` |
| Ingresses | `k8s_events` | `rules`, `tls`, `status` |
| PVCs | `k8s_events` | `phase`, `storageClassName`, `capacity` |
| Jobs | `k8s_events` | `succeeded`, `failed`, `active` |
| CronJobs | `k8s_events` | `lastScheduleTime`, `active` |
| HPA | `k8s_events` | `currentReplicas`, `desiredReplicas` |
| NetworkPolicies | `k8s_events` | `ingress`, `egress` rules |
| Namespaces | `k8s_events` | `phase` |
| ConfigMaps | `k8s_events` | key changes |
| RBAC (Roles, ClusterRoles, Bindings) | `k8s_events` | subjects, rules |

---

### 4. Prometheus Scraping (via Gateway)

#### 4a. cAdvisor (Container filesystem I/O)
Scraped from kubelet `/metrics/cadvisor` endpoint.

| Metric | Labels | Description |
|--------|--------|-------------|
| `container_fs_reads_total` | `container`, `pod`, `namespace`, `device`, `node` | Container filesystem reads |
| `container_fs_writes_total` | `container`, `pod`, `namespace`, `device`, `node` | Container filesystem writes |
| `container_fs_reads_bytes_total` | same | Bytes read |
| `container_fs_writes_bytes_total` | same | Bytes written |

#### 4b. Kube-State-Metrics
Scraped from `kube-state-metrics.kube-system.svc:8080`. **Note: labels use `node`, `pod`, `namespace` (not `k8s_node_name`, etc.)**

**Pod metrics:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_pod_info` | `pod`, `namespace`, `node`, `host_ip`, `pod_ip` | Pod metadata |
| `kube_pod_status_phase` | `pod`, `namespace`, `phase` | Pod phase (value=1 for current) |
| `kube_pod_status_ready` | `pod`, `namespace`, `condition` | Pod ready condition |
| `kube_pod_status_reason` | `pod`, `namespace`, `reason` (Evicted, NodeLost, etc.) | Pod status reason |
| `kube_pod_container_status_ready` | `pod`, `namespace`, `container` | Container ready (0/1) |
| `kube_pod_container_status_restarts_total` | `pod`, `namespace`, `container` | Container restarts (counter) |
| `kube_pod_container_status_waiting_reason` | `pod`, `namespace`, `container`, `reason` (CrashLoopBackOff, ImagePullBackOff, etc.) | Waiting reason |
| `kube_pod_container_status_terminated_reason` | `pod`, `namespace`, `container`, `reason` (OOMKilled, Error, etc.) | Termination reason |
| `kube_pod_container_resource_requests` | `pod`, `namespace`, `container`, `resource` (cpu/memory), `unit` | Resource requests |
| `kube_pod_container_resource_limits` | `pod`, `namespace`, `container`, `resource`, `unit` | Resource limits |
| `kube_pod_owner` | `pod`, `namespace`, `owner_kind`, `owner_name` | Pod owner reference |

**Node metrics:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_node_status_condition` | `node`, `condition` (Ready, DiskPressure, MemoryPressure, PIDPressure), `status` (true/false/unknown) | Node conditions |
| `kube_node_status_allocatable` | `node`, `resource` (cpu, memory, pods, etc.) | Allocatable resources |
| `kube_node_info` | `node`, `kernel_version`, `os_image`, `container_runtime_version`, `kubelet_version` | Node info |
| `kube_node_spec_taint` | `node`, `key`, `effect`, `value` | Node taints |

**Workload metrics:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_deployment_status_replicas_available` | `deployment`, `namespace` | Available replicas |
| `kube_deployment_status_replicas_ready` | `deployment`, `namespace` | Ready replicas |
| `kube_deployment_status_replicas_unavailable` | `deployment`, `namespace` | Unavailable replicas |
| `kube_deployment_spec_replicas` | `deployment`, `namespace` | Desired replicas |
| `kube_daemonset_status_desired_number_scheduled` | `daemonset`, `namespace` | Desired pods |
| `kube_daemonset_status_number_available` | `daemonset`, `namespace` | Available pods |
| `kube_daemonset_status_number_ready` | `daemonset`, `namespace` | Ready pods |
| `kube_daemonset_status_number_misscheduled` | `daemonset`, `namespace` | Misscheduled pods |
| `kube_statefulset_status_replicas_ready` | `statefulset`, `namespace` | Ready replicas |
| `kube_statefulset_replicas` | `statefulset`, `namespace` | Desired replicas |
| `kube_replicaset_status_ready_replicas` | `replicaset`, `namespace` | Ready replicas |
| `kube_replicaset_spec_replicas` | `replicaset`, `namespace` | Desired replicas |

**HPA metrics:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_horizontalpodautoscaler_status_current_replicas` | `horizontalpodautoscaler`, `namespace` | Current replicas |
| `kube_horizontalpodautoscaler_status_desired_replicas` | `horizontalpodautoscaler`, `namespace` | Desired replicas |
| `kube_horizontalpodautoscaler_spec_max_replicas` | `horizontalpodautoscaler`, `namespace` | Max replicas |
| `kube_horizontalpodautoscaler_spec_min_replicas` | `horizontalpodautoscaler`, `namespace` | Min replicas |
| `kube_horizontalpodautoscaler_status_condition` | `horizontalpodautoscaler`, `namespace`, `condition`, `status` | HPA conditions |

**Storage metrics:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_persistentvolumeclaim_status_phase` | `persistentvolumeclaim`, `namespace`, `phase` (Bound/Pending/Lost) | PVC phase |
| `kube_persistentvolumeclaim_resource_requests_storage_bytes` | `persistentvolumeclaim`, `namespace` | PVC requested size |
| `kube_persistentvolume_status_phase` | `persistentvolume`, `phase` (Bound/Available/Released/Failed) | PV phase |
| `kube_persistentvolume_capacity_bytes` | `persistentvolume` | PV capacity |

**Job/CronJob metrics:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_job_status_failed` | `job_name`, `namespace` | Failed job pods |
| `kube_job_status_succeeded` | `job_name`, `namespace` | Succeeded job pods |
| `kube_job_status_active` | `job_name`, `namespace` | Active job pods |
| `kube_job_complete` | `job_name`, `namespace`, `condition` | Job complete condition |
| `kube_job_failed` | `job_name`, `namespace`, `condition` | Job failed condition |
| `kube_cronjob_status_active` | `cronjob`, `namespace` | Active CronJob runs |
| `kube_cronjob_next_schedule_time` | `cronjob`, `namespace` | Next scheduled time (unix) |

**Service/Endpoint/Ingress:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_endpoint_address` | `endpoint`, `namespace` | Endpoint addresses count |
| `kube_service_info` | `service`, `namespace`, `cluster_ip`, `external_ip` | Service info |
| `kube_ingress_path` | `ingress`, `namespace`, `host`, `path` | Ingress path rules |

**Namespace/RBAC/Quota:**
| Metric | Key Labels | Description |
|--------|-----------|-------------|
| `kube_namespace_status_phase` | `namespace`, `phase` (Active/Terminating) | Namespace phase |
| `kube_resourcequota` | `namespace`, `resource`, `type` (hard/used) | Resource quota |
| `kube_limitrange` | `namespace`, `limitrange`, `resource`, `type` | Limit range |
| `kube_networkpolicy_spec_ingress_rules` | `networkpolicy`, `namespace` | Ingress rules count |
| `kube_serviceaccount_info` | `serviceaccount`, `namespace` | Service account info |

#### 4c. CoreDNS
| Metric | Labels | Description |
|--------|--------|-------------|
| `coredns_dns_requests_total` | `server`, `zone`, `proto`, `type` | DNS request count |
| `coredns_dns_responses_total` | `server`, `zone`, `rcode` | DNS response count |
| `coredns_dns_request_duration_seconds_*` | `server`, `zone` | Request latency histogram |
| `coredns_cache_hits_total` | `server`, `type` | Cache hits |
| `coredns_cache_misses_total` | `server` | Cache misses |
| `coredns_panics_total` | — | CoreDNS panics |

#### 4d. kube-apiserver
| Metric | Labels | Description |
|--------|--------|-------------|
| `apiserver_request_total` | `verb`, `resource`, `code`, `component` | API request count |
| `apiserver_request_duration_seconds_bucket` | `verb`, `resource`, `subresource`, `scope`, `le` | Request latency histogram |
| `apiserver_request_duration_seconds_count` | same | Request count |
| `apiserver_admission_webhook_request_total` | `name`, `operation`, `rejected` | Webhook requests |
| `apiserver_current_inflight_requests` | `request_kind` (mutating/readOnly) | In-flight requests |
| `process_resident_memory_bytes` | — | API server memory |
| `process_cpu_seconds_total` | — | API server CPU |
| `kubernetes_build_info` | `gitVersion`, `gitCommit`, `platform` | K8s version info |

#### 4e. kube-scheduler
All scheduler metrics exposed at `:10259/metrics`

| Metric | Labels | Description |
|--------|--------|-------------|
| `scheduler_scheduling_attempt_duration_seconds_*` | `result`, `profile`, `le` | Scheduling latency |
| `scheduler_pending_pods` | `queue` (active/backoff/unschedulable) | Queued pods count |
| `scheduler_preemption_attempts_total` | — | Preemption attempts |
| `scheduler_schedule_attempts_total` | `result` (scheduled/error/unschedulable) | Scheduling attempts |

#### 4f. kube-controller-manager
All controller manager metrics exposed at `:10257/metrics`

| Metric | Labels | Description |
|--------|--------|-------------|
| `workqueue_depth` | `name` (controller name) | Work queue depth |
| `workqueue_adds_total` | `name` | Items added to queue |
| `workqueue_queue_duration_seconds_*` | `name`, `le` | Queue processing latency |
| `controller_runtime_reconcile_total` | `controller`, `result` | Reconcile loop count |
| `controller_runtime_reconcile_errors_total` | `controller` | Reconcile errors |

---

## Summary: Available Metrics by Alert Category

### Node-Level Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| High CPU | `system_cpu_utilization` | `1 - avg by(k8s_node_name,k8s_cluster)(system_cpu_utilization{state="idle"})` |
| High Memory | `system_memory_utilization` | `system_memory_utilization{state="used"}` |
| High Disk | `k8s_node_filesystem_usage` + `k8s_node_filesystem_capacity` | `k8s_node_filesystem_usage / k8s_node_filesystem_capacity` |
| Node Not Ready | `kube_node_status_condition` | `kube_node_status_condition{condition="Ready",status="true"} == 0` |
| Disk Pressure | `kube_node_status_condition` | `kube_node_status_condition{condition="DiskPressure",status="true"} == 1` |
| Memory Pressure | `kube_node_status_condition` | `kube_node_status_condition{condition="MemoryPressure",status="true"} == 1` |
| Node Unschedulable | `kube_node_spec_taint` | `kube_node_spec_taint{key="node.kubernetes.io/unschedulable"}` |

### Pod-Level Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| CrashLoopBackOff | `kube_pod_container_status_waiting_reason` | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} == 1` |
| High Restart Rate | `kube_pod_container_status_restarts_total` | `increase(kube_pod_container_status_restarts_total[10m]) > 5` |
| Pod Pending | `kube_pod_status_phase` | `kube_pod_status_phase{phase="Pending"} == 1` |
| Pod Failed | `kube_pod_status_phase` | `kube_pod_status_phase{phase="Failed"} == 1` |
| ImagePullBackOff | `kube_pod_container_status_waiting_reason` | `kube_pod_container_status_waiting_reason{reason=~"ImagePullBackOff\|ErrImagePull"} == 1` |
| OOMKilled | `kube_pod_container_status_terminated_reason` | `kube_pod_container_status_terminated_reason{reason="OOMKilled"} == 1` |
| Pod Evicted | `kube_pod_status_reason` | `kube_pod_status_reason{reason="Evicted"} == 1` |

### Container-Level Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| CPU Throttling | `k8s_pod_cpu_limit_utilization` | `k8s_pod_cpu_limit_utilization > 0.25` (proxy via limit utilization) |
| Memory Near Limit | `k8s_pod_memory_limit_utilization` | `k8s_pod_memory_limit_utilization > 0.9` |
| Container Not Ready | `kube_pod_container_status_ready` | `kube_pod_container_status_ready == 0` |
| Container Restart | `kube_pod_container_status_restarts_total` | `increase(kube_pod_container_status_restarts_total[5m]) > 0` |

### Workload Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| Deployment Mismatch | `kube_deployment_status_replicas_available` + `kube_deployment_spec_replicas` | `kube_deployment_spec_replicas - kube_deployment_status_replicas_available > 0` |
| StatefulSet Mismatch | `kube_statefulset_status_replicas_ready` + `kube_statefulset_replicas` | `kube_statefulset_replicas - kube_statefulset_status_replicas_ready > 0` |
| DaemonSet Missing Pods | `kube_daemonset_status_*` | `kube_daemonset_status_desired_number_scheduled - kube_daemonset_status_number_ready > 0` |
| Job Failed | `kube_job_status_failed` | `kube_job_status_failed > 0` |
| HPA At Max | `kube_horizontalpodautoscaler_status_current_replicas` | `kube_horizontalpodautoscaler_status_current_replicas >= kube_horizontalpodautoscaler_spec_max_replicas` |

### Control Plane Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| API Server Latency | `apiserver_request_duration_seconds_bucket` | `histogram_quantile(0.99, rate(apiserver_request_duration_seconds_bucket[5m])) > 1` |
| API Server Errors | `apiserver_request_total` | `rate(apiserver_request_total{code=~"5.."}[5m]) > 0.1` |
| API Inflight High | `apiserver_current_inflight_requests` | `apiserver_current_inflight_requests > 400` |
| Scheduler Unschedulable Pods | `scheduler_pending_pods` | `scheduler_pending_pods{queue="unschedulable"} > 5` |
| Controller Reconcile Errors | `controller_runtime_reconcile_errors_total` | `rate(controller_runtime_reconcile_errors_total[5m]) > 0.1` |
| Work Queue Depth | `workqueue_depth` | `workqueue_depth > 50` |

### Network Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| High Network Errors | `k8s_node_network_errors` | `rate(k8s_node_network_errors[5m]) > 10` |
| DNS Failures | `coredns_dns_responses_total` | `rate(coredns_dns_responses_total{rcode!="NOERROR"}[5m]) > 10` |
| DNS Latency | `coredns_dns_request_duration_seconds_bucket` | `histogram_quantile(0.99, rate(coredns_dns_request_duration_seconds_bucket[5m])) > 1` |
| Service No Endpoints | `kube_endpoint_address` | `kube_endpoint_address == 0` |

### Storage Alerts
| Alert | Best Metric | Query Pattern |
|-------|------------|---------------|
| PV Failed | `kube_persistentvolume_status_phase` | `kube_persistentvolume_status_phase{phase="Failed"} == 1` |
| PVC Pending | `kube_persistentvolumeclaim_status_phase` | `kube_persistentvolumeclaim_status_phase{phase="Pending"} == 1` |
| PVC Lost | `kube_persistentvolumeclaim_status_phase` | `kube_persistentvolumeclaim_status_phase{phase="Lost"} == 1` |

---

## Notes on Label Differences

| Source | Node Label | Pod Label | Namespace Label |
|--------|-----------|-----------|-----------------|
| kubeletstats (`k8s_*`) | `k8s_node_name` | `k8s_pod_name` | `k8s_namespace_name` |
| hostmetrics (`system_*`) | `k8s_node_name` | `k8s_pod_name` | `k8s_namespace_name` |
| kube-state-metrics (`kube_*`) | `node` | `pod` | `namespace` |
| cAdvisor (`container_fs_*`) | `node` | `pod` | `namespace` |
| API server / scheduler / CM | `node` | — | — |
| CoreDNS | — | — | — |

When joining `kube_*` metrics with `k8s_*` or `system_*` metrics, use `kube_node_info` as a bridge:
```promql
kube_node_info * on(node) group_left(k8s_node_name) label_replace(up, "node", "$1", "instance", "([^:]+).*")
```
