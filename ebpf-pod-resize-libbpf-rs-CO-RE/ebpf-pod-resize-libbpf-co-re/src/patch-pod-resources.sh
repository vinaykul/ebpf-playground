#!/bin/bash

pod_name=$1
container_name=$2
resources=$3
pod_ns=${4:default}

patch_str="{\"spec\":{\"containers\":[{\"name\":\"${container_name}\",\"resources\":${resources}}]}}"
kubectl -n ${pod_ns} patch pod ${pod_name} --patch ${patch_str}
exit 0
