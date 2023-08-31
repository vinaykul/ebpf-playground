# eBPF TC hook vs. XDP generic hook perf measurement

This contains empty TC and XDP eBPF program code that returns TC_ACT_OK and XDP_PASS respectively.
Attach program to either TC or XDP generic hook (xdp driver mode for virtio or any NIC w/ support)
and run perf tests to see the overhead of each type of hook.


## Build & Clean

Needs clang, llvm, and libbpf-dev.

Build by running `make`

Clean by running `make clean`


## Perf Setup

VM1 (sender)  ------------> VM2 (receiver)

The below steps are applicable on the receiver (VM2) with default NIC named as `eth0`

TC eBPF hook:
  - To attach tc eBPF program to TC hook of NIC (eth0 by default), run `make tcbpf`
  - To detach tc eBPF program, run `make tcbpfoff`
  - To show tc attach status, run `make tcbpfshow`

XDP generic hook:
  - To attach XDP eBPF program to generic XDP hook of NIC (eth0 by default), run `make xdpgeneric`
  - To detach generic mode XDP eBPF program, run `make xdpgenericoff`

XDP driver mode hook (if supported by NIC):
  - To attach XDP eBPF program to driver mode XDP hook of NIC (eth0 by default), run `make xdpdrv`
  - To detach driver mode XDP eBPF program, run `make xdpdrvoff`
  - To show XDP attach status, run `make xdpshow`


## Sending and Receiving traffic with iperf3

On VM2, run `iperf3 -s -p 23434 -i 60 --logfile /dev/null` (or any available port if 23434 is busy)

On VM1, run `iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60` (replace 192.168.64.5 with IP of your VM2)

## Collecting Kernel CPU profile with eBPF

On VM2, clone Brendan Gregg's FlameGraph git repo:
```bash
git clone https://github.com/brendangregg/FlameGraph && cd FlameGraph
```

Start iperf3 server and in another terminal window, start collecting CPU profile for 70 seconds as shown below:
```bash
profile-bpfcc -K -F 99 -adf 70 --stack-storage-size 256000 > /tmp/out.profile-folded
```

On VM1, start iperf3 sender.
```bash
iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
```

After CPU profile data collection has completed, run the flamegraph script on VM2.
```bash
./flamegraph.pl --colors=java /tmp/out.profile-folded > /tmp/profile.svg
```

## Latency measurement with netperf

On VM2, ensure netserver is running. `ps -ef | grep netserver`

On VM1, run `netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency`



## Perf Test Results - Virtual Machines on Mac M2 Max

### No eBPF or XDP program attached

```bash
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 36642 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.9 GBytes  2.13 Gbits/sec    0   2.86 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.9 GBytes  2.13 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.9 GBytes  2.13 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 55020 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.8 GBytes  2.13 Gbits/sec    0   2.76 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.8 GBytes  2.13 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.8 GBytes  2.12 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 40340 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.8 GBytes  2.12 Gbits/sec    0   2.81 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.8 GBytes  2.12 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.8 GBytes  2.11 Gbits/sec                  receiver

iperf Done.
root@km:~#
root@km:~#
root@km:~#

root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
321,2158,524.31
root@km:~/# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
318,2091,534.63
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
359,2172,513.98
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
360,1918,536.23
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
303,2363,523.40
root@km:~#

```

### XDP driver mode

```bash
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 42558 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.8 GBytes  2.12 Gbits/sec  255   2.74 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.8 GBytes  2.12 Gbits/sec  255             sender
[  5]   0.00-60.05  sec  14.8 GBytes  2.12 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 39272 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.7 GBytes  2.11 Gbits/sec    0   2.79 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.7 GBytes  2.11 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.7 GBytes  2.11 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 34276 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.7 GBytes  2.11 Gbits/sec    0   2.80 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.7 GBytes  2.11 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.7 GBytes  2.10 Gbits/sec                  receiver

iperf Done.
root@km:~#
root@km:~#

root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
304,2411,487.90
root@km:~#
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
313,2247,514.58
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
306,2293,521.02
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
340,1853,532.88
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
342,1943,496.95
root@km:~#

```

### XDP generic mode

```bash
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 45948 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  13.2 GBytes  1.89 Gbits/sec    0   2.77 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  13.2 GBytes  1.89 Gbits/sec    0             sender
[  5]   0.00-60.04  sec  13.2 GBytes  1.89 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 60322 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  13.0 GBytes  1.86 Gbits/sec    0   2.83 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  13.0 GBytes  1.86 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  13.0 GBytes  1.86 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 40062 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  13.0 GBytes  1.86 Gbits/sec    0   2.80 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  13.0 GBytes  1.86 Gbits/sec    0             sender
[  5]   0.00-60.04  sec  13.0 GBytes  1.86 Gbits/sec                  receiver

iperf Done.
root@km:~#
root@km:~#

root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
341,1626,523.29
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
317,1869,530.30
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
384,1869,527.98
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
341,2077,528.96
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
315,3176,489.51
root@km:~#
root@km:~#

```

### eBPF TC hook

```bash
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 37554 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.5 GBytes  2.08 Gbits/sec    0   2.88 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.5 GBytes  2.08 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.5 GBytes  2.08 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 52130 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.6 GBytes  2.09 Gbits/sec    0   2.77 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.6 GBytes  2.09 Gbits/sec    0             sender
[  5]   0.00-60.04  sec  14.6 GBytes  2.09 Gbits/sec                  receiver

iperf Done.
root@km:~# iperf3 -c 192.168.64.5 -p 23434 -i 60 -t 60
Connecting to host 192.168.64.5, port 23434
[  5] local 192.168.64.3 port 50174 connected to 192.168.64.5 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  14.6 GBytes  2.09 Gbits/sec    0   2.85 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  14.6 GBytes  2.09 Gbits/sec    0             sender
[  5]   0.00-60.05  sec  14.6 GBytes  2.09 Gbits/sec                  receiver

iperf Done.
root@km:~#
root@km:~#

root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
328,1751,516.50
root@km:~#
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
276,2145,506.58
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
321,1806,525.73
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
318,1803,535.36
root@km:~# netperf -H 192.168.64.5 -t TCP_RR -- -o min_latency,max_latency,mean_latency
MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 192.168.64.5 () port 0 AF_INET : demo : first burst 0
Minimum Latency Microseconds,Maximum Latency Microseconds,Mean Latency Microseconds
310,2509,514.44
root@km:~#

```



## Perf Test Results - Bare Metal Systems

### No eBPF or XDP program attached

```bash
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 56330 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec   62   1.68 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec   62             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 48558 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.7 GBytes  9.41 Gbits/sec   48   2.08 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.7 GBytes  9.41 Gbits/sec   48             sender
[  5]   0.00-60.04  sec  65.7 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 39018 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  147   1.54 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  147             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#

```

### XDP driver mode

```bash
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 55938 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  195   1.57 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  195             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 40486 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  1662   1.60 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  1662             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 37934 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.7 GBytes  9.41 Gbits/sec   14   2.07 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.7 GBytes  9.41 Gbits/sec   14             sender
[  5]   0.00-60.04  sec  65.7 GBytes  9.40 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#

```

### XDP generic mode

```bash
root@server:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 47124 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  55.0 GBytes  7.87 Gbits/sec  180560    479 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  55.0 GBytes  7.87 Gbits/sec  180560             sender
[  5]   0.00-60.04  sec  55.0 GBytes  7.87 Gbits/sec                  receiver

iperf Done.
root@server:~/perfdata#
root@server:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 37168 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  54.7 GBytes  7.83 Gbits/sec  187825    457 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  54.7 GBytes  7.83 Gbits/sec  187825             sender
[  5]   0.00-60.04  sec  54.7 GBytes  7.82 Gbits/sec                  receiver

iperf Done.
root@server:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 53800 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  54.9 GBytes  7.85 Gbits/sec  172422    587 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  54.9 GBytes  7.85 Gbits/sec  172422             sender
[  5]   0.00-60.04  sec  54.9 GBytes  7.85 Gbits/sec                  receiver

iperf Done.
root@server:~/perfdata#

```

### eBPF TC hook

```bash
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 50948 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  678   2.08 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  678             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 48766 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  206   1.75 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  206             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#
root@sender:~/perfdata# iperf3 -c 10.20.30.40 -p 23434 -i 60 -t 60
Connecting to host 10.20.30.40, port 23434
[  5] local 10.20.30.30 port 42392 connected to 10.20.30.40 port 23434
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  474   1.59 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-60.00  sec  65.8 GBytes  9.41 Gbits/sec  474             sender
[  5]   0.00-60.04  sec  65.8 GBytes  9.41 Gbits/sec                  receiver

iperf Done.
root@sender:~/perfdata#

```
