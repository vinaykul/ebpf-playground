# Prototype eBPF program to snoop on pod exec syscalls
# requires bpfcc-tools, crictl, jq, bcc, kubernetes
# To run: sudo python3 podsnoop.py

import os
import re
import json
import multiprocessing
from bcc import BPF
from ctypes import *
#TODO: Use cri_api instead of crictl
#from cri_api.channel import Channel
from kubernetes import client, config, watch

POD_SNOOP_eBPF_CODE = r"""
#define BUF_SIZE 32
struct command {
    char cmd[BUF_SIZE];
};
BPF_HASH(resize_containers_map, u64, struct command);
TRACEPOINT_PROBE(syscalls, sys_enter_execve) {
    char task_cmd[BUF_SIZE];
    u64 cgroup_id = bpf_get_current_cgroup_id();
    struct command *val = resize_containers_map.lookup(&cgroup_id);
    if (val != NULL) {
        u8 is_equal = 1;
        bpf_get_current_comm(&task_cmd, sizeof(task_cmd));
        for (u8 i = 0; i < BUF_SIZE; i++) {
            if (task_cmd[i] != val->cmd[i]) {
                is_equal = 0;
                break;
            }
            if (task_cmd[i] == '\0' || val->cmd[i] == '\0') {
                break;
            }
        }
        if (is_equal) {
            bpf_trace_printk("{ \"cgroup_id\": \"%llu\", \"command\": \"%s\" }", cgroup_id, task_cmd);
        }
    }
    return 0;
}
"""

BUF_SIZE = 32
class Tcommand( Structure ):
   _fields_ = [ ("cmd", c_char * BUF_SIZE) ]

nodename = os.uname()[1]
config.load_incluster_config()
#channel = Channel("unix:///containerd/containerd.sock")

bpf = BPF(text = POD_SNOOP_eBPF_CODE)
resize_containers_map = bpf["resize_containers_map"]


def watch_k8s_pods():
    node_name = os.environ.get('MY_NODE_NAME', '127.0.0.1')
    print("DBG: Watching pods on node: '{}'".format(node_name))
    field_selector = 'spec.nodeName='+node_name
    w = watch.Watch()
    for event in w.stream(func=client.CoreV1Api().list_pod_for_all_namespaces, field_selector=field_selector):
        if (event['object'].status) and (cs := event['object'].status.container_statuses) and (pod_name := event['object'].metadata.name):
            #TODO: While cs[0] (ugh!) is good enough for demo, we need to check container name against pod annotations for resize candidate.
            if (cs[0]) and (cs[0].ready) and (cs[0].started):
                pod_ns = event['object'].metadata.namespace
                print("DBG POD: %s CONTAINER: %s CONTAINER-ID: %s is ready!" % (pod_name, cs[0].name, cs[0].container_id))
                if not (v1_pod := client.CoreV1Api().read_namespaced_pod(name=pod_name, namespace=pod_ns.strip('\"'))):
                    continue
                if not v1_pod.metadata.annotations:
                    continue
                if not (resize_annotation_value := v1_pod.metadata.annotations["ebpf-resize"]):
                    continue
                cid = re.split(r"//", cs[0].container_id)[1]
                if not (cgroup_path := os.popen("find /sys/fs/cgroup/unified/kubepods -type d -name %s 2>/dev/null" % cid).read().strip()):
                    if not (cgroup_path := os.popen("find /sys/fs/cgroup/kubepods -type d -name %s 2>/dev/null" % cid).read().strip()):
                        continue
                if not (cgroup_id := os.popen("ls -ladi %s | awk '{print $1}' 2>/dev/null" % cgroup_path).read().strip()):
                    continue
                if not (resize_json := json.loads(resize_annotation_value)):
                    continue
                #TODO: handle multiple commands
                if (len(resize_json["commands"]) == 0) or not (resize_trigger := resize_json["commands"][0]):
                    continue
                print("DBG: POD: %s CONTAINER-ID: %s EVENT: %s CGROUP-ID: %s requests eBPF resize on '%s'." % (pod_name, cgroup_id, event['type'], cid, resize_trigger))
                if (event['type'] == "ADDED") or ((event['type'] == "MODIFIED") and (v1_pod.metadata.deletion_timestamp == None)):
                    resize_cmd = Tcommand()
                    resize_cmd.cmd = str.encode(resize_trigger)
                    resize_containers_map[c_int(int(cgroup_id))] = resize_cmd
                if (event['type'] == "REMOVED") or ((event['type'] == "MODIFIED") and (v1_pod.metadata.deletion_timestamp != None)):
                    try:
                       del resize_containers_map[c_int(int(cgroup_id))]
                    except KeyError:
                        pass

def handle_ebpf_snoop_trace():
    print("DBG: eBPF pod resizer started on node '{}'".format(nodename))
    while True:
        try:
            (task, pid, cpu, flags, ts, msg) = bpf.trace_fields()
            pod_name = os.popen("nsenter -t %s -u hostname 2>/dev/null" % pid).read().strip()
            if (not pod_name) or (pod_name == nodename):
                continue
            if (msg_json := json.loads(msg)):
                print("DBG: POD: '{}', CGROUP-ID: '{}', CMD: '{}'".format(pod_name, msg_json['cgroup_id'], msg_json['command']))
                container_id_cmd = "basename $(find /sys/fs/cgroup -inum %s | grep kubepods | grep unified)" % msg_json['cgroup_id']
                if not (container_id := os.popen("%s 2>/dev/null" % container_id_cmd).read().strip()):
                    container_id_cmd = "basename $(find /sys/fs/cgroup -inum %s | grep kubepods)" % msg_json['cgroup_id']
                    if not (container_id := os.popen("%s 2>/dev/null" % container_id_cmd).read().strip()):
                        continue
                pod_ns = os.popen("crictl inspect %s | jq '.status.labels.\"io.kubernetes.pod.namespace\"' 2>/dev/null" % container_id).read().strip()
                if not pod_ns:
                    continue
                if not (v1_pod := client.CoreV1Api().read_namespaced_pod(name=pod_name, namespace=pod_ns.strip('\"'))):
                    continue
                if not (resize_annotation_value := v1_pod.metadata.annotations["ebpf-resize"]):
                    continue
                if not (resize_json := json.loads(resize_annotation_value)):
                    continue
                if not (container_name := os.popen("crictl inspect %s | jq .status.metadata.name 2>/dev/null" % container_id).read().strip()):
                    continue
                container_name = container_name.strip('\"')
                if (container_name == resize_json["cname"]) and (msg_json['command'] in resize_json["commands"]):
                    if (resources_json := json.loads(resize_json["resize"])):
                        req = resources_json["requests"]
                        lim = resources_json["limits"]
                    if (resized_resources := client.V1ResourceRequirements(requests=req,limits=lim)):
                        for c in v1_pod.spec.containers:
                            if c.name == container_name:
                                c.resources = resized_resources
                                break
                    print("DBG: eBPF detected trigger command '{}'. Resizing pod '{}' container '{}'!".format(msg_json['command'], pod_name, container_name))
                    client.CoreV1Api().patch_namespaced_pod(name=pod_name, namespace=pod_ns.strip('\"'), body=v1_pod)
        except ValueError:
            continue


pod_watcher = multiprocessing.Process(target=watch_k8s_pods)
snoop_handler = multiprocessing.Process(target=handle_ebpf_snoop_trace)

pod_watcher.start()
snoop_handler.start()

snoop_handler.join()
pod_watcher.join()

