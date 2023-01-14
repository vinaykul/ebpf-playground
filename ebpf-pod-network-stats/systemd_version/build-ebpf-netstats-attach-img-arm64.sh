#!/bin/bash -x

make clean
docker rmi -f skiibum/ebpf-netstats-attach-arm64:poc

make all
docker image build -t skiibum/ebpf-netstats-attach-arm64:poc -f ebpf-network-stats-attach.Dockerfile .
