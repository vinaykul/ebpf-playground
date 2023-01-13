# attach_ebpf_stats_prog.py: This program attaches a tc eBPF stats gathering program
# to the ingress tc hook of a Kubernetes pod's veth that sits in the default namespace.
# Environment variables:
#    eBPF_PROGRAM_NAME: Path to the tc eBPF stats program to attach
#    eBPF_SECTION_NAME: Name of section in the eBPF program to attach
# Usage: python3 attach_ebpf_stats_prog.py

import os
import subprocess
from pyroute2 import NDB

# Default constants
TX_STATS_eBPF_PROGRAM_NAME="./obj/bpf_network_stats.o"
TX_STATS_eBPF_SECTION_NAME="pod_net_stats_tx"

eBPF_program_name=TX_STATS_eBPF_PROGRAM_NAME
eBPF_section_name=TX_STATS_eBPF_SECTION_NAME

# Find all the veth interfaces created by containerd (NetNS name begins with 'cni-')
def get_cni_veth_interfaces():
    ndb = NDB()
    iflist = []
    ifaces = ndb.interfaces.dump()
    ifaces.select_records(state='up', kind='veth')
    ifaces.select_fields('ifname', 'link_netnsid')
    for iface in ifaces:
        #print("Interface_NAME: {} , Interface_NetNSID: {}".format(iface['ifname'], iface['link_netnsid']))
        netnscmd = "ip netns list-id nsid {}".format(iface['link_netnsid'])
        r = subprocess.Popen(netnscmd, shell=True, stdout=subprocess.PIPE)
        output = r.stdout.read().decode().strip()
        if "cni-" in output:
            iflist.append(iface)
    return iflist


# Find all the veth interfaces that are targets for eBPF stats program attachment
def get_ebpf_stats_target_interfaces(iflist):
    target_iflist = []
    for iface in iflist:
        tcshowcmd = "tc filter show dev {} ingress | grep {}".format(iface['ifname'], TX_STATS_eBPF_SECTION_NAME)
        r = subprocess.Popen(tcshowcmd, shell=True, stdout=subprocess.PIPE)
        output = r.stdout.read().decode().strip()
        if len(output) == 0:
            target_iflist.append(iface)
    return target_iflist


# Attach eBPF stats program to target interfaces
def attach_ebpf_stats_to_target_interfaces(target_iflist):
    for iface in target_iflist:
        tcqdiscshowcmd = "tc qdisc show dev {} | grep clsact".format(iface['ifname'])
        r = subprocess.Popen(tcqdiscshowcmd, shell=True, stdout=subprocess.PIPE)
        output = r.stdout.read().decode().strip()
        if len(output) == 0:
            tcqdiscaddcmd = "tc qdisc add dev {} clsact".format(iface['ifname'])
            r = subprocess.Popen(tcqdiscaddcmd, shell=True, stdout=subprocess.PIPE)
            output = r.stdout.read().decode().strip()
            if len(output) == 0:
                print("tc classifier action successfully added for interface {}".format(iface['ifname']))
            else:
                print("Failed to add tc classifier action on  interface {}".format(iface['ifname']))
            tcfilteraddcmd = "tc filter add dev {} ingress bpf da obj {} sec {}".format(iface['ifname'],
                    eBPF_program_name, eBPF_section_name)
            print(tcfilteraddcmd)
            r = subprocess.Popen(tcqdiscaddcmd, shell=True, stdout=subprocess.PIPE)
            output = r.stdout.read().decode().strip()
            if len(output) == 0:
                print("eBPF program '{}' successfully attached to interface {}".format(eBPF_program_name, iface['ifname']))
            else:
                print("Failed to attach eBPF program '{}' to interface {}".format(eBPF_program_name, iface['ifname']))


# Main function
def main():
    iflist = get_cni_veth_interfaces()
    #print(iflist)

    target_iflist = get_ebpf_stats_target_interfaces(iflist)
    #print(target_iflist)

    attach_ebpf_stats_to_target_interfaces(target_iflist)


if __name__ == "__main__":
    if "eBPF_PROGRAM_NAME" in os.environ:
        eBPF_program_name = os.getenv("eBPF_PROGRAM_NAME")
    if "eBPF_SECTION_NAME" in os.environ:
        eBPF_section_name = os.getenv("eBPF_SECTION_NAME")
    main()
