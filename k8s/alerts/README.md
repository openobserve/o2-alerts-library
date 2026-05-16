# Kubernetes Alert Library — OpenObserve

Exported from OpenObserve org `default`, folder `7461312355696140288`.

**Total alerts: 76**

---

## Categories

| Category | Count |
|---|---|
| [node/](#node-10-alerts) | 10 |
| [pod/](#pod-7-alerts) | 7 |
| [container/](#container-4-alerts) | 4 |
| [cluster/](#cluster-5-alerts) | 5 |
| [storage/](#storage-5-alerts) | 5 |
| [network/](#network-4-alerts) | 4 |
| [workload/](#workload-8-alerts) | 8 |
| [control-plane/](#control-plane-6-alerts) | 6 |
| [security/](#security-4-alerts) | 4 |
| [resource-optimization/](#resource-optimization-5-alerts) | 5 |
| [app-performance/](#app-performance-2-alerts) | 2 |
| [k8s-events/](#k8s-events-16-alerts) | 16 |

---

## node/ (10 alerts)

| Alert Name | File |
|---|---|
| node_critical_cpu_utilization | [node/node_critical_cpu_utilization.json](node/node_critical_cpu_utilization.json) |
| node_critical_disk_usage | [node/node_critical_disk_usage.json](node/node_critical_disk_usage.json) |
| node_critical_memory_usage | [node/node_critical_memory_usage.json](node/node_critical_memory_usage.json) |
| node_disk_pressure | [node/node_disk_pressure.json](node/node_disk_pressure.json) |
| node_high_cpu_utilization | [node/node_high_cpu_utilization.json](node/node_high_cpu_utilization.json) |
| node_high_disk_usage | [node/node_high_disk_usage.json](node/node_high_disk_usage.json) |
| node_high_memory_usage | [node/node_high_memory_usage.json](node/node_high_memory_usage.json) |
| node_memory_pressure | [node/node_memory_pressure.json](node/node_memory_pressure.json) |
| node_not_ready | [node/node_not_ready.json](node/node_not_ready.json) |
| node_unschedulable | [node/node_unschedulable.json](node/node_unschedulable.json) |

---

## pod/ (7 alerts)

| Alert Name | File |
|---|---|
| pod_crashloop_backoff | [pod/pod_crashloop_backoff.json](pod/pod_crashloop_backoff.json) |
| pod_evicted | [pod/pod_evicted.json](pod/pod_evicted.json) |
| pod_failed_state | [pod/pod_failed_state.json](pod/pod_failed_state.json) |
| pod_high_restart_rate | [pod/pod_high_restart_rate.json](pod/pod_high_restart_rate.json) |
| pod_image_pull_backoff | [pod/pod_image_pull_backoff.json](pod/pod_image_pull_backoff.json) |
| pod_oom_killed | [pod/pod_oom_killed.json](pod/pod_oom_killed.json) |
| pod_pending_too_long | [pod/pod_pending_too_long.json](pod/pod_pending_too_long.json) |

---

## container/ (4 alerts)

| Alert Name | File |
|---|---|
| container_cpu_limit_high | [container/container_cpu_limit_high.json](container/container_cpu_limit_high.json) |
| container_memory_near_limit | [container/container_memory_near_limit.json](container/container_memory_near_limit.json) |
| container_not_ready | [container/container_not_ready.json](container/container_not_ready.json) |
| container_restarted | [container/container_restarted.json](container/container_restarted.json) |

---

## cluster/ (5 alerts)

| Alert Name | File |
|---|---|
| apiserver_high_latency | [cluster/apiserver_high_latency.json](cluster/apiserver_high_latency.json) |
| certificate_expiry_warning | [cluster/certificate_expiry_warning.json](cluster/certificate_expiry_warning.json) |
| cluster_cpu_capacity_high | [cluster/cluster_cpu_capacity_high.json](cluster/cluster_cpu_capacity_high.json) |
| cluster_memory_capacity_high | [cluster/cluster_memory_capacity_high.json](cluster/cluster_memory_capacity_high.json) |
| cluster_pod_count_high | [cluster/cluster_pod_count_high.json](cluster/cluster_pod_count_high.json) |

---

## storage/ (5 alerts)

| Alert Name | File |
|---|---|
| pv_failed | [storage/pv_failed.json](storage/pv_failed.json) |
| pv_usage_high | [storage/pv_usage_high.json](storage/pv_usage_high.json) |
| pvc_lost | [storage/pvc_lost.json](storage/pvc_lost.json) |
| pvc_pending | [storage/pvc_pending.json](storage/pvc_pending.json) |
| storage_volume_under_utilized | [storage/storage_volume_under_utilized.json](storage/storage_volume_under_utilized.json) |

---

## network/ (4 alerts)

| Alert Name | File |
|---|---|
| dns_high_latency | [network/dns_high_latency.json](network/dns_high_latency.json) |
| dns_resolution_failures_high | [network/dns_resolution_failures_high.json](network/dns_resolution_failures_high.json) |
| node_network_errors_high | [network/node_network_errors_high.json](network/node_network_errors_high.json) |
| service_no_ready_endpoints | [network/service_no_ready_endpoints.json](network/service_no_ready_endpoints.json) |

---

## workload/ (8 alerts)

| Alert Name | File |
|---|---|
| cronjob_missed_schedule | [workload/cronjob_missed_schedule.json](workload/cronjob_missed_schedule.json) |
| daemonset_pods_not_scheduled | [workload/daemonset_pods_not_scheduled.json](workload/daemonset_pods_not_scheduled.json) |
| deployment_replica_mismatch | [workload/deployment_replica_mismatch.json](workload/deployment_replica_mismatch.json) |
| hpa_at_max_replicas | [workload/hpa_at_max_replicas.json](workload/hpa_at_max_replicas.json) |
| hpa_unable_to_scale | [workload/hpa_unable_to_scale.json](workload/hpa_unable_to_scale.json) |
| job_backoff_limit_exceeded_events | [workload/job_backoff_limit_exceeded_events.json](workload/job_backoff_limit_exceeded_events.json) |
| job_failed | [workload/job_failed.json](workload/job_failed.json) |
| statefulset_replica_mismatch | [workload/statefulset_replica_mismatch.json](workload/statefulset_replica_mismatch.json) |

---

## control-plane/ (6 alerts)

| Alert Name | File |
|---|---|
| admission_webhook_failures_high | [control-plane/admission_webhook_failures_high.json](control-plane/admission_webhook_failures_high.json) |
| apiserver_error_rate_high | [control-plane/apiserver_error_rate_high.json](control-plane/apiserver_error_rate_high.json) |
| apiserver_inflight_requests_high | [control-plane/apiserver_inflight_requests_high.json](control-plane/apiserver_inflight_requests_high.json) |
| controller_queue_processing_slow | [control-plane/controller_queue_processing_slow.json](control-plane/controller_queue_processing_slow.json) |
| controller_reconcile_errors_high | [control-plane/controller_reconcile_errors_high.json](control-plane/controller_reconcile_errors_high.json) |
| controller_workqueue_depth_high | [control-plane/controller_workqueue_depth_high.json](control-plane/controller_workqueue_depth_high.json) |

---

## security/ (4 alerts)

| Alert Name | File |
|---|---|
| image_from_untrusted_registry | [security/image_from_untrusted_registry.json](security/image_from_untrusted_registry.json) |
| namespace_without_network_policy | [security/namespace_without_network_policy.json](security/namespace_without_network_policy.json) |
| pod_missing_resource_limits | [security/pod_missing_resource_limits.json](security/pod_missing_resource_limits.json) |
| unauthorized_api_access_high | [security/unauthorized_api_access_high.json](security/unauthorized_api_access_high.json) |

---

## resource-optimization/ (5 alerts)

| Alert Name | File |
|---|---|
| container_cpu_over_provisioned | [resource-optimization/container_cpu_over_provisioned.json](resource-optimization/container_cpu_over_provisioned.json) |
| container_memory_over_provisioned | [resource-optimization/container_memory_over_provisioned.json](resource-optimization/container_memory_over_provisioned.json) |
| container_resource_under_requested | [resource-optimization/container_resource_under_requested.json](resource-optimization/container_resource_under_requested.json) |
| node_low_utilization | [resource-optimization/node_low_utilization.json](resource-optimization/node_low_utilization.json) |
| pods_without_resource_requests | [resource-optimization/pods_without_resource_requests.json](resource-optimization/pods_without_resource_requests.json) |

---

## app-performance/ (2 alerts)

| Alert Name | File |
|---|---|
| go_gc_pause_high | [app-performance/go_gc_pause_high.json](app-performance/go_gc_pause_high.json) |
| go_gc_rate_high | [app-performance/go_gc_rate_high.json](app-performance/go_gc_rate_high.json) |

---

## k8s-events/ (16 alerts)

| Alert Name | File |
|---|---|
| azure_maintenance_scheduled_events | [k8s-events/azure_maintenance_scheduled_events.json](k8s-events/azure_maintenance_scheduled_events.json) |
| azure_storage_provisioning_failed_events | [k8s-events/azure_storage_provisioning_failed_events.json](k8s-events/azure_storage_provisioning_failed_events.json) |
| coredns_unreachable_events | [k8s-events/coredns_unreachable_events.json](k8s-events/coredns_unreachable_events.json) |
| high_warning_event_rate | [k8s-events/high_warning_event_rate.json](k8s-events/high_warning_event_rate.json) |
| hpa_metric_unavailable_events | [k8s-events/hpa_metric_unavailable_events.json](k8s-events/hpa_metric_unavailable_events.json) |
| image_pull_errors_events | [k8s-events/image_pull_errors_events.json](k8s-events/image_pull_errors_events.json) |
| image_pull_secret_missing_events | [k8s-events/image_pull_secret_missing_events.json](k8s-events/image_pull_secret_missing_events.json) |
| network_not_ready_events | [k8s-events/network_not_ready_events.json](k8s-events/network_not_ready_events.json) |
| node_condition_change_events | [k8s-events/node_condition_change_events.json](k8s-events/node_condition_change_events.json) |
| node_drain_failed_events | [k8s-events/node_drain_failed_events.json](k8s-events/node_drain_failed_events.json) |
| node_shutdown_events | [k8s-events/node_shutdown_events.json](k8s-events/node_shutdown_events.json) |
| oom_killing_events | [k8s-events/oom_killing_events.json](k8s-events/oom_killing_events.json) |
| pod_sandbox_failed_events | [k8s-events/pod_sandbox_failed_events.json](k8s-events/pod_sandbox_failed_events.json) |
| pod_scheduling_failures_events | [k8s-events/pod_scheduling_failures_events.json](k8s-events/pod_scheduling_failures_events.json) |
| pod_unhealthy_probe_events | [k8s-events/pod_unhealthy_probe_events.json](k8s-events/pod_unhealthy_probe_events.json) |
| volume_mount_failures_events | [k8s-events/volume_mount_failures_events.json](k8s-events/volume_mount_failures_events.json) |
