#!/bin/bash -x

docker rmi -f skiibum/ebpf-pod-resize-amd64:demo
docker image build -t skiibum/ebpf-pod-resize-amd64:demo -f ebpf-pod-resize-demo.Dockerfile .
