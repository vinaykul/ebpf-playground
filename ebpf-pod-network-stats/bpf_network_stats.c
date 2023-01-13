// SPDX-License-Identifier: GPL-2.0
// Author: Vinay Kulkarni <@vinaykul>

//#include "vmlinux.h"
#include <linux/bpf.h>
#include <bpf/bpf_endian.h>
#include <bpf/bpf_helpers.h>
#include "bpf_network_stats_maps.h"
#include "bpf_elf_helpers.h"

#include <stdio.h>
#include <stdint.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>

#if 0
#include <linux/in.h>
//#include <bpf/bpf_tracing.h>
#endif

#if 0
#define MAX_POD_INTERFACES 400

struct bpf_elf_map SEC("maps") pod_net_stats_tx_map = {
    .type        = BPF_MAP_TYPE_HASH,
    .size_key    = sizeof(struct tx_net_stats_key_t),
    .size_value  = sizeof(struct tx_net_stats_t),
    .max_elem    = MAX_POD_INTERFACES,
    .pinning     = PIN_GLOBAL_NS,
};
#endif

SEC("pod_net_stats_tx")
int tc_pod_net_stats_tx(struct __sk_buff *skb)
{
	char msg[] = "==>> SRC: %x BYTES=%u\n";
	uint64_t cgid = bpf_skb_cgroup_id(skb);
	void *data = (void *)(long)skb->data;
	void *data_end = (void *)(long)skb->data_end;
	uint64_t len = (uint64_t)(skb->data_end - skb->data);

        if (data + sizeof(struct ethhdr) + sizeof(struct iphdr)  < data_end) {
                struct ethhdr *eth = data;
                struct iphdr *ip = (data + sizeof(struct ethhdr));
		bpf_trace_printk(msg, sizeof(msg), bpf_ntohl(ip->saddr), len);
        }
        return TC_ACT_OK;
}

char __license[] SEC("license") = "GPL";
