#!/bin/bash -x

pushd ebpf-netstats-program
make clean
make all
popd

docker rmi -f skiibum/ebpf-netstats-attach-arm64:poc
docker image build -t skiibum/ebpf-netstats-attach-arm64:poc -f ebpf-netstats-docker-img/ebpf-netstats-attach.Dockerfile .
