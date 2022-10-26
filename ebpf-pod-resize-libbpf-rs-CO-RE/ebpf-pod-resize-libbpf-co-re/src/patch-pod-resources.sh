#!/bin/bash

pod_name=$1
container_name=$2
resources=$3

patch_str="{\"spec\":{\"containers\":[{\"name\":\"${container_name}\",\"resources\":${resources}}]}}"
kubectl patch pod ${pod_name} --patch ${patch_str}
exit 0

