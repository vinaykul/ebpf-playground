# attach_ebpf_stats_prog.py: This program attaches a tc eBPF stats gathering program
# to the ingress tc hook of a Kubernetes pod's veth that sits in the default namespace.
# Environment variables:
#    eBPF_PROGRAM_NAME: Path to the tc eBPF stats program to attach
#    eBPF_SECTION_NAME: Name of section in the eBPF program to attach
# Usage: python3 attach_ebpf_stats_prog.py

import datetime
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
    print(">>get_cni_veth_interfaces")
    ndb = NDB()
    iflist = []
    ifaces = ndb.interfaces.dump()
    ifaces.select_records(state='up', kind='veth')
    ifaces.select_fields('ifname', 'link_netnsid')
    for iface in ifaces:
        print("Interface_NAME: {} , Interface_NetNSID: {}".format(iface['ifname'], iface['link_netnsid']))
        netnscmd = "nsenter -t 1 -m -u -n -i ip netns list-id nsid {}".format(iface['link_netnsid'])
        print(netnscmd)
        r = subprocess.Popen(netnscmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = r.stdout.read().decode().strip()
        err = r.stderr.read().decode().strip()
        print("DBG-OUT-ip-netns-list: '{}'".format(output))
        print("DBG-ERR-ip-netns-list: '{}'".format(err))
        if len(err) > 0:
            print("FAIL: 'ip netns list-id' for interface '{}' failed ERROR='{}'".format(iface['ifname'], err))
            return None
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
        print(">>DBG-attach-stats: IFNAME='{}'".format(iface['ifname']))
        tcqdiscshowcmd = "tc qdisc show dev {} | grep clsact".format(iface['ifname'])
        r = subprocess.Popen(tcqdiscshowcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = r.stdout.read().decode().strip()
        err = r.stderr.read().decode().strip()
        print("DBG-OUT-tc-qdisc-show: '{}'".format(output))
        print("DBG-ERR-tc-qdisc-show: '{}'".format(err))
        if len(err) > 0:
            print("FAIL: 'tc qdisc show' for interface '{}' failed ERROR='{}'".format(iface['ifname']), err)
            return
        # Do 'tc qdisc add clsact'
        if len(output) == 0:
            tcqdiscaddcmd = "tc qdisc add dev {} clsact".format(iface['ifname'])
            #TODO: Add helper function to execute and eliminate duplicate code
            r = subprocess.Popen(tcqdiscaddcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = r.stdout.read().decode().strip()
            err = r.stderr.read().decode().strip()
            print("DBG-OUT-tc-qdisc-add: '{}'".format(output))
            print("DBG-ERR-tc-qdisc-add: '{}'".format(err))
            if len(err) > 0:
                print("FAIL: 'tc qdisc add' for interface '{}' failed ERROR='{}'".format(iface['ifname']), err)
                return
            if len(output) == 0:
                print("tc classifier action successfully added for interface {}".format(iface['ifname']))
        # Attach eBPF stats program to veth ingress
        tcfilteraddcmd = "tc filter add dev {} ingress bpf da obj {} sec {}".format(iface['ifname'], eBPF_program_name, eBPF_section_name)
        print(tcfilteraddcmd)
        r = subprocess.Popen(tcfilteraddcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = r.stdout.read().decode().strip()
        err = r.stderr.read().decode().strip()
        print("DBG-OUT-tc-filter-add: '{}'".format(output))
        print("DBG-ERR-tc-filter-add: '{}'".format(err))
        if len(err) > 0:
            print("FAIL: 'tc filter add' for interface '{}' failed ERROR='{}'".format(iface['ifname']), err)
            return
        if len(output) == 0:
            now = datetime.datetime.now()
            print("{}: eBPF program '{}' successfully attached to interface {}".format(now, eBPF_program_name, iface['ifname']))


# Main function
def main():
    iflist = get_cni_veth_interfaces()
    print(iflist)

    if iflist is not None:
        target_iflist = get_ebpf_stats_target_interfaces(iflist)
        print(target_iflist)

        if target_iflist is not None:
            attach_ebpf_stats_to_target_interfaces(target_iflist)


if __name__ == "__main__":
    if "eBPF_PROGRAM_NAME" in os.environ:
        eBPF_program_name = os.getenv("eBPF_PROGRAM_NAME")
    if "eBPF_SECTION_NAME" in os.environ:
        eBPF_section_name = os.getenv("eBPF_SECTION_NAME")
    main()
