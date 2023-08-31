#
# Build tc and xdp eBPF programs
# Needs llvm, clang, bpfcc-tools, linux-headers-$(uname -r), libbpf-dev
# NOTE: This Makefile has been tested only on Ubuntu 22.04
#

CLANG=clang
CLANG_FLAGS=-g -O2 -Wall -target bpf
CLANG_INCLUDES=/usr/include/$(shell uname -p)-linux-gnu/
BPFSRC=$(wildcard *.c)
BPFOBJ=$(BPFSRC:.c=_bpf.o)
DEFAULT_NIC=eth0

.PHONY: bpf

bpf: $(BPFOBJ)

%_bpf.o: %.c
	$(CLANG) -I $(CLANG_INCLUDES) $(CLANG_FLAGS) -c $^ -o $@

clean:
	rm -f $(BPFOBJ)

xdpgeneric:
	ip link set dev $(DEFAULT_NIC) xdpgeneric obj xdp_ingress_bpf.o sec xdpingress

xdpgenericoff:
	ip link set dev $(DEFAULT_NIC) xdpgeneric off

xdpdrv:
	ip link set dev $(DEFAULT_NIC) xdpdrv obj xdp_ingress_bpf.o sec xdpingress

xdpdrvoff:
	ip link set dev $(DEFAULT_NIC) xdpdrv off

xdpshow:
	ip link show dev $(DEFAULT_NIC)

tcbpf:
	tc qdisc add dev $(DEFAULT_NIC) clsact || true
	tc filter add dev $(DEFAULT_NIC) ingress bpf da obj tc_ingress_bpf.o sec tcingress

tcbpfoff:
	tc filter del dev $(DEFAULT_NIC) ingress

tcbpfshow:
	tc filter show dev $(DEFAULT_NIC) ingress
