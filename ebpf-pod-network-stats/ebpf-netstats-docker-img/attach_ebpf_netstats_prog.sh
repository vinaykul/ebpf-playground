#!/usr/bin/bash -x

# Set this environment variable to provide location of the eBPF stats program
#export eBPF_PROGRAM_NAME=""

# Set this environment variable to provide eBPF section name of stats program
#export eBPF_SECTION_NAME=""

#TODO: Investigate why 'retval' from bpftrace is garbage when using upstream bits vs. 'GODEBUG=1 make all' bits
#      Calling attach_ebpf_netstats_prog.py still works since it aims to attach eBPF program to all containerd
#      generated network namespaces ('cni-' prefix). Specifying only certain CNI network interfaces (via pod
#      annotations or some other means) is a possible future work item if that is desired.
#if [ $1 == 0 ]; then
    python3 /attach_ebpf_netstats_prog.py
#fi
