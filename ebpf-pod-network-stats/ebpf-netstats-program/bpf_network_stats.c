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
