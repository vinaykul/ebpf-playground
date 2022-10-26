# ebpf-pod-resize

This code is meant to illustrate how eBPF can help proactively initiate in-place resize of pod resources
for use cases such as the Remote Development Environment. The defining characteristic of such an use case
is the spikes in resource needs.

A reactive approach such as VPA is not the best option for such use case. eBPF can help resize the pod
with significantly lower latency based on user specified conditions.

NOTE: This code is for illustration purposes only and not meant for any production use. It was written
to illustrate and demonstrate an idea.
