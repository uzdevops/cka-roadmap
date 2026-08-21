## An address that is not on any interface

Pods get real interfaces with real IPs. A Service's ClusterIP is different:
it exists only as rules. On every node, **kube-proxy** watches Services and
EndpointSlices and writes rules that say "a packet to this IP:port → rewrite
the destination to one of these Pod IP:ports". No process listens on a
ClusterIP; `ping` to one goes nowhere.

```
Pod A ── 10.96.12.7:80 ──┐
                          ├── iptables on the node: DNAT to 10.244.2.5:8080 (or .6, or .7)
                          └── the packet leaves with a Pod destination; the CNI carries it
```

## Three ranges, again

| Range | Default | Owner |
|---|---|---|
| Pod CIDR | `10.244.0.0/16` (Flannel convention) | CNI + controller manager |
| Service CIDR | `10.96.0.0/12` | `--service-cluster-ip-range` on the API server |
| node ports | `30000-32767` | `--service-node-port-range` on the API server |

They must not overlap, and the Service range is entirely virtual.

```bash
ps -ef | grep kube-apiserver | grep -o -- '--service-cluster-ip-range=[^ ]*'
kubectl get svc -A          # every ClusterIP is inside that range
```

## What kube-proxy writes

```bash
kubectl get svc db -o wide
# NAME   TYPE        CLUSTER-IP     PORT(S)    SELECTOR
# db     ClusterIP   10.96.12.7     3306/TCP   app=db
kubectl get endpointslices -l kubernetes.io/service-name=db
# ... ENDPOINTS 10.244.2.5,10.244.1.9
```

On any node, iptables mode:

```bash
iptables -t nat -L KUBE-SERVICES -n | grep 10.96.12.7
#  KUBE-SVC-XYZ  tcp  --  0.0.0.0/0  10.96.12.7  /* default/db cluster IP */ tcp dpt:3306
iptables -t nat -L KUBE-SVC-XYZ -n
#  KUBE-SEP-AAA  ... statistic mode random probability 0.5   <- pick endpoint 1 half the time
#  KUBE-SEP-BBB  ...                                          <- else endpoint 2
iptables -t nat -L KUBE-SEP-AAA -n
#  DNAT  ... to:10.244.2.5:3306
```

`KUBE-SERVICES` → one `KUBE-SVC-*` chain per Service → one `KUBE-SEP-*`
chain per endpoint with the DNAT. Random selection with equal probability
is the load balancing. A NodePort adds a `KUBE-NODEPORTS` entry matching the
node port that jumps to the same `KUBE-SVC-*` chain; that is the whole
difference.

In **IPVS** mode the same information is a kernel virtual server table
(`ipvsadm -Ln`) - better at scale, more algorithms (round-robin, least
connections), same idea. In **nftables** mode (the newer default) the rules
are nft sets and maps.

```bash
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep -i "proxy mode"
kubectl get cm kube-proxy -n kube-system -o yaml | grep -A1 "mode:"
```

## Following a packet

1. Pod A (10.244.1.2) connects to `db:3306`; CoreDNS says `db` = 10.96.12.7.
2. The packet leaves A's namespace for the node's bridge with destination
   10.96.12.7.
3. On the node, the `nat` PREROUTING hook runs `KUBE-SERVICES`; the
   destination is rewritten to 10.244.2.5:3306.
4. The node routes 10.244.2.5 toward node02 like any Pod packet (routes or
   overlay - the CNI's job).
5. The reply from 10.244.2.5 is un-NATed by conntrack on the way back, so A
   sees it come from 10.96.12.7.

Step 3 is the only place the Service exists. If kube-proxy on **A's node** is
broken, A cannot reach any Service - while Pod B on another node can. That
asymmetry is the diagnostic.

## Why Services break

| Symptom | Look at |
|---|---|
| DNS resolves, connection hangs from **every** node | endpoints empty (selector/readiness) → `kubectl get endpoints` |
| hangs from **one** node only | kube-proxy Pod on that node: `kubectl get pods -n kube-system -o wide -l k8s-app=kube-proxy` and its logs |
| works by ClusterIP, not by NodePort | firewall on the node port; `externalTrafficPolicy: Local` with no Pod on that node |
| worked, stopped after a kube-proxy change | wrong `--config` path or ConfigMap in the DaemonSet - logs say `open ...: no such file` |
| Pod on the same node cannot reach the Service | `net.bridge.bridge-nf-call-iptables` is 0 |

:::exam-tip
`iptables -t nat -L KUBE-SERVICES -n | grep <clusterIP>` on a node proves
in one line whether kube-proxy has programmed the Service there. No line =
kube-proxy is not doing its job on that node; a line = the Service exists
and the problem is endpoints or the CNI path beyond.
:::

## Check yourself

1. Where does a ClusterIP "exist", and which component puts it there?
2. Describe the three-chain structure kube-proxy creates for one Service in
   iptables mode.
3. Pods on node02 cannot reach any Service; Pods on node01 can. Which
   component, where?
