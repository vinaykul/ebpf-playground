# Author: Vinay Kulkarni <@vinaykul>

all: skel
	cargo build
	cp src/get-podns-podname-ctrname.sh target/debug/
	cp src/patch-pod-resources.sh target/debug/

bpf: vmlinux
	cargo libbpf build

skel: bpf
	cargo libbpf gen

vmlinux:
	bpftool btf dump file /sys/kernel/btf/vmlinux format c > ./src/bpf/vmlinux.h

clean:
	cargo clean
	rm -f src/bpf/*.rs 
