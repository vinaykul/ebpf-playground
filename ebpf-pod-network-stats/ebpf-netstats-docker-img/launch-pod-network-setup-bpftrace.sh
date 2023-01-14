#!/bin/bash -xe

#
# NOTE: Currently, we have a limitation - we need debug version of containerd
#       To build debug version of containerd:
#         git clone containerd/containerd
#         cd containerd
#         <checkout desired containerd branch>
#         GODEBUG=1 make all
#         <replace upstream/retail containerd and friends from bin/
#

bpftrace --unsafe -e 'uretprobe:/hostusrbin/containerd:"github.com/containerd/containerd/pkg/cri/server.(*criService).setupPodNetwork" { system("/attach_ebpf_netstats_prog.sh %d", retval); }'

