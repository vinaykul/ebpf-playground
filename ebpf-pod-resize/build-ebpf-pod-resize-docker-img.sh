#!/bin/bash -x

docker rmi -f skiibum/ebpf-pod-resize:demo
docker image build -t skiibum/ebpf-pod-resize:demo -f ebpf-pod-resize-demo.Dockerfile .
