#!/usr/bin/bash

#TODO: Update from env variables
TX_STATS_eBPF_PROGRAM_NAME="./obj/bpf_network_stats.o"
TX_STATS_eBPF_SECTION_NAME="pod_net_stats_tx"

echo $(date '+%T.%N')
for ifname in $(nsenter -t 1 -m -u -n -i ip -o -d link show type veth | grep "cni-" | awk '{print $2}' | cut -d@ -f1)
do
    tc -o filter show dev $ifname ingress | grep $TX_STATS_eBPF_SECTION_NAME > /dev/null 2>&1
    if [ $? -ne 0 ]
    then
        tc qdisc add dev $ifname clsact
        tc filter add dev $ifname ingress bpf da obj $TX_STATS_eBPF_PROGRAM_NAME sec $TX_STATS_eBPF_SECTION_NAME
    fi
done
echo $(date '+%T.%N')
