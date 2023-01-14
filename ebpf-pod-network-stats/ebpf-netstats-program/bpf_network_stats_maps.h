// SPDX-License-Identifier: GPL-2.0
// Author: Vinay Kulkarni <@vinaykul>

#ifndef __BFP_NETSTATS_H
#define __BFP_NETSTATS_H

struct tx_net_stats_key_t {
        __u32 saddr;
} __attribute__((packed, aligned(4)));

struct tx_net_stats_t {
        __u64 tx_bytes;
        __u64 tx_pkts;
} __attribute__((packed, aligned(8)));

#endif /* __BFP_NETSTATS_H */
