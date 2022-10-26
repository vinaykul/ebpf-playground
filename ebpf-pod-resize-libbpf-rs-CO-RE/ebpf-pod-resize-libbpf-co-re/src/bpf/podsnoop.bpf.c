// SPDX-License-Identifier: GPL-2.0
// Author: Vinay Kulkarni <@vinaykul>

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "podsnoop.h"

#define MAX_NUM_CONTAINERS 4096

struct pod_exec_event _pxevent = {0};

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, MAX_NUM_CONTAINERS);
	__type(key, u64);
	__type(value, struct pod_command);
} resize_containers_map SEC(".maps");

struct {
        __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
        __uint(key_size, sizeof(u32));
        __uint(value_size, sizeof(u32));
} pod_exec_events SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_execve")
int podsnoop(void *ctx) {
	u64 cgroup_id = bpf_get_current_cgroup_id();
/*
struct pod_exec_event pxev = {};
pxev.cgroup_id = cgroup_id;
bpf_get_current_comm(&pxev.cgroup_cmd, sizeof(pxev.cgroup_cmd));
long rv = bpf_perf_event_output(ctx, &pod_exec_events, BPF_F_CURRENT_CPU, &pxev, sizeof(pxev));
if (rv != 0) {
  bpf_printk("VVDBG-FAIL: podsnoop call to bpf_perf_event_output failed. ErrCode: %d\n", rv);
} else {
  bpf_printk("VVDBG-SUCCESS: podsnoop call to bpf_perf_event_output failed. ErrCode: %d\n", rv);
}*/

	struct pod_command *val = bpf_map_lookup_elem(&resize_containers_map, &cgroup_id);
	if (val != NULL) {
		u8 is_equal = 1;
		struct pod_exec_event pxevent = {};
		bpf_get_current_comm(&pxevent.cgroup_cmd, sizeof(pxevent.cgroup_cmd));
		//TODO: Find a more efficient way. Maybe 'val->cmd' should be u64 hash
		for (u8 i = 0; i < BUF_SIZE; i++) {
			if (pxevent.cgroup_cmd[i] != val->cmd[i]) {
				is_equal = 0;
				break;
			}
			if (pxevent.cgroup_cmd[i] == '\0' || val->cmd[i] == '\0') {
				break;
			}
		}
		if (is_equal) {
			pxevent.cgroup_id = cgroup_id;
			u64 id = bpf_get_current_pid_tgid();
			pxevent.cgroup_pid = id & 0xFFFFFFFF;
			long rv = bpf_perf_event_output(ctx, &pod_exec_events, BPF_F_CURRENT_CPU, &pxevent, sizeof(pxevent));
			if (rv != 0) {
				bpf_printk("DBG: podsnoop call to bpf_perf_event_output failed. ErrCode: %d\n", rv);
			}
			bpf_printk("VDBG: { \"cgroup_id\": \"%llu\", \"cgroup_pid\": \"%lu\", \"command\": \"%s\" }",
					cgroup_id,pxevent.cgroup_pid, pxevent.cgroup_cmd);
		}
	}
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
