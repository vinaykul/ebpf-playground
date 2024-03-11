#!/bin/bash -e

RED='\033[0;31m'
ORANGE='\033[0;33m'
BLUE='\033[1;94m'
PURPLE='\033[1;35m'
PURPLEL='\033[0;35m'
GREEN='\033[1;92m'
NC='\033[0m'

NETWORK_IDENTITY=${1:-12345}

function num_to_hex_str() {
  local size=$1
  local value=$2
  local hexstr=$(printf "%0${size}x" $value)
  local spaced_hexstr=$(echo $hexstr | sed -E 's/(..)/\1 /g')
  local reversed_hexstr=$(echo $spaced_hexstr | awk '{for(i=NF;i>=1;i--) printf "%s ",$i}')
  echo $reversed_hexstr
}

#echo "Looking up bank-auditor container-id."
C_ID=$(crictl ps | grep bank-auditor | awk '{print $1}')

echo -e "👀 ${PURPLE}Looking up cgroup-id of bank-auditor container (container-id=${C_ID}) 👀${NC}"
CG_ID=$(ls -ldi $(find /sys/fs/cgroup/kubepods.slice/kubepods-besteffort.slice/ -type d | grep ${C_ID}) | awk '{print $1}')

BPF_MAP_KEY=$(num_to_hex_str 16 ${CG_ID})
BPF_MAP_VALUE=$(num_to_hex_str 8 ${NETWORK_IDENTITY})

sed s/__AUDITOR_POD_IDENTITY__/\"${NETWORK_IDENTITY}\"/ z-ciliumid/ciliumid-auditor.yaml.tmpl > z-ciliumid/ciliumid-auditor.yaml
echo -e "🛠  ${PURPLE}Creating CiliumIdentity object (cilium-id=${NETWORK_IDENTITY}) for bank-auditor hostNetwork pod (cgroup-id=${CG_ID}) 🛠${NC}"
printf "   ☑️   " && kubectl create -f ~/demo/z-ciliumid/ciliumid-auditor.yaml
if [ $? -ne 0 ]; then
  echo -e "${RED}ERROR: Unable to create CiliumIdentity for bank-auditor pod. ERROR_CODE=$?${NC}"
fi

echo -e "🐝 ${PURPLE}Adding network identity of bank-auditor container to HOST_PROCESS_NETID BPF map${NC} 🐝"
HP_MAP_ID=$(bpftool map list | grep host_process | awk '{print $1}' | cut -d: -f1)
BPFTOOL_CMD="bpftool map update id ${HP_MAP_ID} key hex ${BPF_MAP_KEY} value hex ${BPF_MAP_VALUE}"
echo -e "${NC}   ☑️   cmd: '${BPFTOOL_CMD}'${NC}"
eval "${BPFTOOL_CMD}"
if [ $? -eq 0 ]; then
  echo -e "✅ ${BLUE}Success! bank-auditor network identity ${NETWORK_IDENTITY} is now associated with cgroup-id ${CG_ID} ✅${NC}"
fi
