#!/bin/bash

cgroup_id=$1
cgroup_pid=$2

pod_name=$(nsenter -t ${cgroup_pid} -u hostname 2>/dev/null)
if [ -z "${pod_name}" ]; then
  exit 2
fi

ctr_id=$(basename $(find /sys/fs/cgroup -inum ${cgroup_id} | grep kubepods | grep unified) 2>/dev/null)
if [ -z "${ctr_id}" ]; then
  ctr_id=$(basename $(find /sys/fs/cgroup -inum ${cgroup_id} | grep kubepods) 2>/dev/null)
fi
if [ -z "${ctr_id}" ]; then
  exit 2
fi

pod_ns=$(crictl inspect ${ctr_id} | jq '.status.labels."io.kubernetes.pod.namespace"' 2>/dev/null)
if [ -z "${pod_ns}" ]; then
  exit 2
fi

ctr_name=$(crictl inspect ${ctr_id} | jq .status.metadata.name 2>/dev/null)
if [ -z "${ctr_name}" ]; then
  exit 2
fi

printf '{"pod_ns": %s, "pod_name": "%s", "container_name": %s}' ${pod_ns} ${pod_name} ${ctr_name}
exit 0

