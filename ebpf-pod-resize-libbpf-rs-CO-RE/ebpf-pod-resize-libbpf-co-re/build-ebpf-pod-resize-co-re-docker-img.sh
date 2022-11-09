#!/bin/bash -x

make clean && make all

docker rmi -f skiibum/ebpf-pod-resize-co-re:demo
docker image build -t skiibum/ebpf-pod-resize-co-re:demo -f ebpf-pod-resize-co-re.Dockerfile .
