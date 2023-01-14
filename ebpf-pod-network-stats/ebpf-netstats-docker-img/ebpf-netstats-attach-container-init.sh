#!/bin/bash -xe

apt-get update -y
apt-get install -y linux-headers-$(uname -r)
