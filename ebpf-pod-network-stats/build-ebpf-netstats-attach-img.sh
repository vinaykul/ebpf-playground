#!/bin/bash -x

cpu_arch="amd64"
if [[ "$(arch)" == "aarch64" ]]; then
    cpu_arch="arm64"
fi

pushd ebpf-netstats-program
make clean
make all
popd

docker rmi -f skiibum/ebpf-netstats-attach-${cpu_arch}:poc
docker image build -t skiibum/ebpf-netstats-attach-${cpu_arch}:poc -f ebpf-netstats-docker-img/ebpf-netstats-attach.Dockerfile .
