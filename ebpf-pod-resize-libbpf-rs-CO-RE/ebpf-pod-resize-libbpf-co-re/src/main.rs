// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Author: Vinay Kulkarni <@vinaykul>
// NOTE: This code is my 'rust learning exercise' (going to be very ugly)
// This is a good example of how NOT to write rust code (not even for "just a demo") :)

use anyhow::{bail, Result};
use core::option::Option;
use core::time::Duration;
use libbpf_rs::{PerfBufferBuilder, Map, MapFlags};
use plain::Plain;
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::env;
use std::process::{Command};
use std::str;
use std::str::FromStr;
use std::thread;

use futures::prelude::*;
use k8s_openapi::apimachinery::pkg::api::resource::Quantity;
use k8s_openapi::api::core::v1::{Pod, ResourceRequirements};
use kube::{
    api::{Api, ListParams, ResourceExt, Patch, PatchParams},
    runtime::{watcher, WatchStreamExt},
    Client,
};

mod podsnoop {
    include!(concat!(env!("OUT_DIR"), "/podsnoop.skel.rs"));
}

use podsnoop::*;

fn bump_memlock_rlimit() -> Result<()> {
    let rlimit = libc::rlimit {
        rlim_cur: 128 << 20,
        rlim_max: 128 << 20,
    };

    if unsafe { libc::setrlimit(libc::RLIMIT_MEMLOCK, &rlimit) } != 0 {
        bail!("Failed to increase memlock rlimit");
    }

    Ok(())
}

unsafe impl Plain for podsnoop_bss_types::pod_exec_event {}

#[tokio::main]
async fn resize_k8s_pod(pod_ns: &str, pod_name: &str, container_name: &str) -> Result<()> {
    let client = Client::try_default().await?;
    let pods: Api<Pod> = Api::namespaced(client, pod_ns);
    let v1_pod = pods.get(pod_name).await?;
    let ann = v1_pod.annotations();
    if ann.get("ebpf-resize").is_some() {
        let resize_json: Value = serde_json::from_str(ann.get("ebpf-resize").unwrap())?;
        println!("DBG: resizing pod NS: '{}' NAME: '{}' CNAME: '{}' RESIZE: '{:?}'", pod_ns, pod_name, container_name, resize_json["resize"]);
        let mut pod_resize_cmd = Command::new("./patch-pod-resources.sh");
        pod_resize_cmd.arg(pod_name).arg(container_name).arg(resize_json["resize"].as_str().unwrap()).arg(pod_ns);
        let pod_rszout = pod_resize_cmd.output().expect("failed to execute process");
        println!("DBG: RSZOUT: '{:?}'", pod_rszout);

        /* TODO: Figure out how to use the library API.
         *       To the person responsible for documenting kube-rs, who hurt you? ;)
        println!("DBG: V1P: '{:?}'", v1_pod);
        for mut c in &v1_pod.spec.unwrap().containers.clone() {
            if c.name != container_name {
                continue;
            }
            let mut cresources = c.clone().resources.unwrap();
            println!("CRES: '{:?}'", cresources);

            let resizelim = resize.clone()["limits"];
            let resizereq = resize.clone()["requests"];
            let memlim = resizelim.clone()["memory"];
            let memreq = resizereq.clone()["memory"];
            println!("DBG: ML '{:?}' MR '{:?}'", memlim, memreq);

            let mut lim = BTreeMap::new();
            let mut req = BTreeMap::new();
            lim.insert("memory", Quantity("5Gi".into()));
            req.insert("memory", Quantity("5Gi".into()));
            let newlim: Option<BTreeMap<String, Quantity>> = Some(lim);
            //lim.insert("memory": Quantity(resize["limits"]["memory"]));
            //let newresources = ResourceRequirements{limits: lim, requests: req};
            let newresources = ResourceRequirements{limits: , requests: "{{"requests":{{"memory":"5Gi"}}"}
            let patch = json!({
                "spec": {
                    "containers": [{
                        "name": container_name,
                        "resources": cresources
                    }]
                }
            });
            println!("VDBG PP '{:?}'", patch);
            let patchparams = PatchParams::default();
            let ppp = pods.patch(pod_name, &patchparams, &Patch::Merge(&patch)).await?;
            println!("VDBG PPP '{:?}'", ppp);
        }*/
    }
    Ok(())
}

fn handle_pod_snoop_event(_cpu: i32, data: &[u8]) {
    let mut px_event = podsnoop_bss_types::pod_exec_event::default();
    plain::copy_from_bytes(&mut px_event, data).expect("Data buffer was too short");
    let cgroup_id = px_event.cgroup_id.to_string();
    let cgroup_pid = px_event.cgroup_pid.to_string();
    let cgroup_cmd = std::str::from_utf8(&px_event.cgroup_cmd).unwrap();
    //println!("DBG pod_snoop_event: cgroup_id='{}' cgroup_pid='{}' cgroup_id_cmd='{}'", cgroup_id, cgroup_pid, cgroup_cmd);

    let mut pod_info_cmd = Command::new("./get-podns-podname-ctrname.sh");
    pod_info_cmd.arg(cgroup_id).arg(cgroup_pid);
    let pod_info = pod_info_cmd.output().expect("failed to execute process");
    let pod_info_str = String::from_utf8(pod_info.stdout).unwrap();
    //println!("DBG POD_INFO '{}'", pod_info_str);

    if pod_info_str.len() == 0 {
        return
    }
    let pod_info_json: Value = serde_json::from_str(&pod_info_str).unwrap();
    let pod_ns = pod_info_json["pod_ns"].as_str().unwrap();
    let pod_name = pod_info_json["pod_name"].as_str().unwrap();
    let container_name = pod_info_json["container_name"].as_str().unwrap();

    println!("VDBG: resizing pod NS: '{}' NAME: '{}' CNAME: '{}'", pod_ns, pod_name, container_name);
    _ = resize_k8s_pod(pod_ns, pod_name, container_name);
}

fn handle_lost_events(cpu: i32, count: u64) {
    eprintln!("Lost {} events on CPU {}", count, cpu);
}


/*
const BUF_SIZE: usize = 32;
#[repr(C)]
pub struct pod_command {
    pub cmd: [libc::c_char; BUF_SIZE],
}*/
fn create_resize_bpf_map_entry(cid: String, cmd: String, rc_map: &mut Map) -> Result<()> {
    let cg_path;
    let splt = cid.split("//");
    let vec: Vec<&str> = splt.collect();
    let dir_name = vec[1];
    let mut find_dir = Command::new("find");
    find_dir.arg("/sys/fs/cgroup/unified/kubepods").arg("-type").arg("d").arg("-name").arg(dir_name);
    let cg_path_out = find_dir.output().expect("failed to execute process");
    if cg_path_out.stdout.len() == 0 {
        let mut find_dir_cgv1 = Command::new("find");
        find_dir_cgv1.arg("/sys/fs/cgroup/kubepods").arg("-type").arg("d").arg("-name").arg(dir_name);
        let cg_path_out_v1 = find_dir_cgv1.output().expect("failed to execute process");
        cg_path = String::from_utf8(cg_path_out_v1.stdout).unwrap();
    } else {
        cg_path = String::from_utf8(cg_path_out.stdout).unwrap();
    }
    let mut ls_cgid = Command::new("ls");
    ls_cgid.arg("-ladi").arg(cg_path.trim());
    let ls_cgid_out = ls_cgid.output().expect("failed to execute process");
    let ls_cg_out = String::from_utf8(ls_cgid_out.stdout).unwrap();
    let cgsplt = ls_cg_out.split(" ");
    let veccg: Vec<&str> = cgsplt.collect();
    let cgroup_id = veccg[0];
    println!("DBG: cgroup_id: '{}' , cmd: '{}'", cgroup_id,  cmd);

    let cgroup_id_key = u64::from_str(cgroup_id).unwrap();
    let cmd_bytes = cmd.as_bytes();
    //TODO: Is there a better way than this ugly hack?!
    let mut cmd_value: [u8; 32] = [0,0,0,0,0,0,0,0,  0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,];
    for i in 0..cmd_bytes.len() {
        cmd_value[i] = cmd_bytes[i];
    }
    let result = rc_map.update(&cgroup_id_key.to_ne_bytes(), &cmd_value, MapFlags::ANY);
    println!("DBG: rc_map update done. result: '{:?}'", result);
    return Ok(())
}

fn handle_k8s_pod(p: Pod, rc_map: &mut Map) -> Result<()> {
    //TODO: Fix watch field selector and avoid node_name check here
    let my_node_name = env::var("MY_NODE_NAME").expect("$MY_NODE_NAME is not set");
    println!("DBG: Pod: '{}'", p.name_any());
    if let Some(spec) = &p.spec {
        if spec.node_name != Some(my_node_name) {
            return Ok(())
        }
    }

    let ann = p.annotations();
    if ann.get("ebpf-resize").is_some() {
        let resize_json: Value = serde_json::from_str(ann.get("ebpf-resize").unwrap())?;
        let cname = resize_json["cname"].as_str().unwrap();
        if let Some(status) = &p.status {
            if status.container_statuses == None {
                return Ok(())
            }
            for cs in status.clone().container_statuses.unwrap() {
                if cname == cs.name {
                    if cs.container_id == None {
                        continue
                    }
                    let cmds: Vec<Value> = serde_json::from_value(resize_json["commands"].clone())?;
                    for cmd in cmds {
                        //TODO: BUGBUG: Fix map value to hold a list of cmds instead of one cmd
                        _ = create_resize_bpf_map_entry(cs.clone().container_id.unwrap(), cmd.as_str().unwrap().to_string(), rc_map);
                    }
                }
            }
        }
    }
    return Ok(())
}

#[tokio::main]
#[you_can::turn_off_the_borrow_checker]
async fn load_ebpf_tracer_and_watch_k8s_pods() -> Result<()> {
    let client = Client::try_default().await?;
    let api = Api::<Pod>::all(client);
    let lp = ListParams::default();

    let mut skel_builder = PodsnoopSkelBuilder::default();
    skel_builder.obj_builder.debug(true);
    let mut open_skel = skel_builder.open()?;
    let mut skel = open_skel.load()?;
    skel.attach()?;

    // I need access to both maps.
    // I know wut i'm doing and you don't so fluck you borrow checker >:)
    let mut skel1 = unsafe { ::you_can::borrow_unchecked(&mut skel) };
    let mut skel2 = unsafe { ::you_can::borrow_unchecked(&mut skel) };
    let mut binding = skel1.maps_mut();
    let rc_map = binding.resize_containers_map();

    let perf_thread = thread::spawn(move || -> Result<()> {
        let perf = PerfBufferBuilder::new(skel2.maps().pod_exec_events())
            .sample_cb(handle_pod_snoop_event)
            .lost_cb(handle_lost_events)
            .build()?;
        loop {
            perf.poll(Duration::from_millis(100))?;
        }
    });

    /*
    if let Some(label) = &app.selector {
        lp = lp.labels(label);
    }*/
    //TODO: Fix watch field selector and avoid node_name check when handling pods
    let mut podstream = watcher(api, lp).applied_objects().boxed();
    while let Some(pod) = podstream.try_next().await? {
        println!("DBG: Pod: '{}'", pod.name_any());
        _ = handle_k8s_pod(pod, rc_map);
    }

    perf_thread.join().unwrap();

    Ok(())
}

fn main() -> Result<()> {
    bump_memlock_rlimit()?;

    _ = load_ebpf_tracer_and_watch_k8s_pods();
    println!("DBG: DONE-DONE");

    Ok(())
}
