# SPDX-License-Identifier: MIT
# Copyright (c) 2022 The Authors.

# Authors: Vinay Kulkarni <@vinaykul>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:The above copyright
# notice and this permission notice shall be included in all copies or
# substantial portions of the Software.THE SOFTWARE IS PROVIDED "AS IS",
# WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.

FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get install -y bpfcc-tools bpftrace python3 python3-pyroute2

#TODO: Replace this demo bpf_network_stats.o with desired (real) eBPF stats program
COPY obj/bpf_network_stats.o /obj/
COPY attach_ebpf_stats_prog.sh attach_ebpf_stats_prog.py init-container.sh launch-pod-network-setup-bpftrace.sh /

CMD /launch-pod-network-setup-bpftrace.sh
