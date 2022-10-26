//! # libbpf-rs
//!
//! `libbpf-rs` is a safe, idiomatic, and opinionated wrapper around
//! [libbpf](https://github.com/libbpf/libbpf/).
//!
//! libbpf-rs, together with `libbpf-cargo` (libbpf cargo plugin) allow you
//! to write Compile-Once-Run-Everywhere (CO-RE) eBPF programs. Note this document
//! uses "eBPF" and "BPF" interchangeably.
//!
//! More information about CO-RE is [available
//! here](https://facebookmicrosites.github.io/bpf/blog/2020/02/19/bpf-portability-and-co-re.html).
//!
//! ## High level workflow
//!
//! 1. Create new rust project (via `cargo new` or similar) at path `$PROJ_PATH`
//! 1. Create directory `$PROJ_PATH/src/bpf`
//! 1. Write CO-RE bpf code in `$PROJ_PATH/src/bpf/${MYFILE}.bpf.c`, where `$MYFILE` may be any
//!    valid filename. Note the `.bpf.c` extension is required.
//! 1. Create a [build script](https://doc.rust-lang.org/cargo/reference/build-scripts.html)
//!    that builds and generates a skeleton module using `libbpf_cargo::SkeletonBuilder`
//! 1. Write your userspace code by importing and using the generated module. Import the
//!    module by using the [path
//!    attribute](https://doc.rust-lang.org/reference/items/modules.html#the-path-attribute).
//!    Your userspace code goes in `$PROJ_PATH/src/` as it would in a normal rust project.
//! 1. Continue regular rust workflow (ie `cargo build`, `cargo run`, etc)
//!
//! ## Alternate workflow
//!
//! While using the skeleton is recommended, it is also possible to directly use libbpf-rs.
//!
//! 1. Follow steps 1-3 of "High level workflow"
//! 1. Generate a BPF object file. Options include manually invoking `clang`, creating a build
//!    script to invoke `clang`, or using `libbpf-cargo` cargo plugins.
//! 1. Write your userspace code in `$PROJ_PATH/src/` as you would a normal rust project and point
//!    libbpf-rs at your BPF object file
//! 1. Continue regular rust workflow (ie `cargo build`, `cargo run`, etc)
//!
//! ## Design
//!
//! libbpf-rs models various "phases":
//! ```text
//!                from_*()        load()
//!                  |               |
//!                  v               v
//!    ObjectBuilder ->  OpenObject  -> Object
//!                          ^            ^
//!                          |            |
//!              <pre-load modifications> |
//!                                       |
//!                            <post-load interactions>
//! ```
//!
//! The entry point into libbpf-rs is [`ObjectBuilder`]. `ObjectBuilder` helps open the BPF object
//! file. After the object file is opened, you are returned an [`OpenObject`] where you can
//! perform all your pre-load operations. Pre-load means before any BPF maps are created or BPF
//! programs are loaded and verified by the kernel. Finally, after the BPF object is loaded, you
//! are returned an [`Object`] instance where you can read/write to BPF maps, attach BPF programs
//! to hooks, etc.
//!
//! You _must_ keep the [`Object`] alive the entire duration you interact with anything inside the
//! BPF object it represents. This is further documented in [`Object`] documentation.
//!
//! ## Example
//!
//! This is probably the best way to understand how libbpf-rs and libbpf-cargo work together.
//!
//! [See example here](https://github.com/libbpf/libbpf-rs/tree/master/examples/runqslower).

#![warn(missing_debug_implementations)]

mod error;
mod iter;
mod link;
mod map;
mod object;
mod perf_buffer;
mod print;
mod program;
pub mod query;
mod ringbuf;
/// Used for skeleton -- an end user may not consider this API stable
#[doc(hidden)]
pub mod skeleton;
mod tc;
mod util;

pub use libbpf_sys;

pub use crate::error::{Error, Result};
pub use crate::iter::Iter;
pub use crate::link::Link;
pub use crate::map::{Map, MapFlags, MapType, OpenMap};
pub use crate::object::{Object, ObjectBuilder, OpenObject};
pub use crate::perf_buffer::{PerfBuffer, PerfBufferBuilder};
pub use crate::print::{get_print, set_print, PrintCallback, PrintLevel};
pub use crate::program::{OpenProgram, Program, ProgramAttachType, ProgramType};
pub use crate::ringbuf::{RingBuffer, RingBufferBuilder};
pub use crate::tc::{
    TcAttachPoint, TcHook, TcHookBuilder, TC_CUSTOM, TC_EGRESS, TC_H_CLSACT, TC_H_INGRESS,
    TC_H_MIN_EGRESS, TC_H_MIN_INGRESS, TC_INGRESS,
};
pub use crate::util::num_possible_cpus;
