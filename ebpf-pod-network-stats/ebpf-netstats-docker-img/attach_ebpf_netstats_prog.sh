#!/usr/bin/bash -x

# Set this environment variable to provide location of the eBPF stats program
#export eBPF_PROGRAM_NAME=""

# Set this environment variable to provide eBPF section name of stats program
#export eBPF_SECTION_NAME=""

if [ $1 == 0 ]; then
    python3 /attach_ebpf_netstats_prog.py
fi
