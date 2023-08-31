#include <linux/bpf.h>
#include <linux/pkt_cls.h>

#ifndef __section
#define __section(NAME)                  \
        __attribute__((section(NAME), used))
#endif

__section("tcingress")
int tc_ingress_noop(struct __sk_buff *skb) {
        return TC_ACT_OK;
}

char __license[] __section("license") = "GPL";
