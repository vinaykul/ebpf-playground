// SPDX-License-Identifier: GPL-2.0
// Author: Vinay Kulkarni <@vinaykul>

#ifndef __PODSNOOP_H
#define __PODSNOOP_H

#define BUF_SIZE 32

struct pod_command {
	char cmd[BUF_SIZE];
};

struct pod_exec_event {
	u64 cgroup_id;
	u32 cgroup_pid;
	u8 cgroup_cmd[BUF_SIZE];
};

#endif /* __PODSNOOP_H */
