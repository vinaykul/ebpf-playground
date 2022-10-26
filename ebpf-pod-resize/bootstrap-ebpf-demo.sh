#!/bin/bash -x

# Supported only for Ubuntu 20.04 LTS (may work with 22.04)

cd $HOME
mkdir -p $HOME/tmp
cd $HOME/tmp

# Install required packages
apt-get update -y
apt-get upgrade -y
apt-get install -y build-essential jq curl wget vim

# Install go 1.19.2
if [[ "$(uname -m)" == "aarch64" ]]; then
  wget https://go.dev/dl/go1.19.2.linux-arm64.tar.gz
  tar -xf go1.19.2.linux-arm64.tar.gz
  mv go /usr/local/
else
  wget https://go.dev/dl/go1.19.2.linux-amd64.tar.gz
  tar -xf go1.19.2.linux-amd64.tar.gz
  mv go /usr/local/
fi

# Install and configure containerd, crictl, kubectl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
apt-get update -y && apt-get install -y containerd cri-tools kubectl kubernetes-cni
cat > /etc/crictl.yaml << EOF
runtime-endpoint: unix:///var/run/containerd/containerd.sock
image-endpoint: unix:///var/run/containerd/containerd.sock
timeout: 2
debug: false
pull-image-on-create: false
EOF

# Clone in-place resize k8s repo
mkdir -p ~/go/src/k8s.io
pushd ~/go/src/k8s.io
git clone https://github.com/vinaykul/kubernetes k8s-pod-resize
pushd ~/go/src/k8s.io/k8s-pod-resize
git checkout restart-free-pod-vertical-scaling
./hack/install-etcd.sh

# Clone and build cfssl
export GOPATH=$HOME/go
export GOROOT=/usr/local/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
mkdir -p ~/go/src/github.com/cloudflare
pushd ~/go/src/github.com/cloudflare
git clone https://github.com/cloudflare/cfssl
cd cfssl
make all
cp bin/cfssl /usr/sbin/
cp bin/cfssljson /usr/sbin/

# Install bpftool
apt-get update -y
apt-get install -y linux-tools-common linux-tools-$(uname -r)

set +x
echo "Please add go root and go path to your .profile"
echo "    export GOPATH=$HOME/go"
echo "    export GOROOT=/usr/local/go"
echo "    export PATH=$GOPATH/bin:$GOROOT/bin:$PATH"
