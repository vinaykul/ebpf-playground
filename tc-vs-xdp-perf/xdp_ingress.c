#include <linux/bpf.h>
#include <linux/pkt_cls.h>

#ifndef __section
#define __section(NAME)                  \
        __attribute__((section(NAME), used))
#endif

__section("xdpingress")
int xdp_ingress_noop(struct xdp_md *ctx) {
        return XDP_PASS;
}

char __license[] __section("license") = "GPL";
