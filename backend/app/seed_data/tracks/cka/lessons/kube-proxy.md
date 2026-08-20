## The problem kube-proxy solves

Pods have IPs, but Pods are replaced all the time. A Service gives a set of
Pods one stable virtual IP - the **ClusterIP** - and a name. The catch: that
ClusterIP is not assigned to any interface anywhere. No process listens on it.
It exists only as a rule on every node that says "traffic to this IP, rewrite
it to one of these Pod IPs".

kube-proxy is the component that writes and maintains those rules. It runs on
**every node** as a DaemonSet, watches Services and EndpointSlices through the
API server, and programs the node's packet filter accordingly.

```
Pod A ──▶ 10.96.0.10:80 (ClusterIP) ──iptables/IPVS on this node──▶ 10.244.1.5:8080 (a Pod behind the Service)
```

## Modes

| Mode | How | Notes |
|---|---|---|
| **iptables** | one chain of rules per Service; random selection among endpoints | the default; fine up to a few thousand Services |
| **IPVS** | kernel virtual server with hash tables | scales better, more load-balancing algorithms; needs the `ip_vs` modules |
| nftables | newer replacement for iptables rules | becoming the default in recent releases |
| userspace | old, slow, gone | historical |

```bash
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep -i "proxy mode"
# Using iptables Proxier / Using ipvs Proxier
```

The mode lives in kube-proxy's ConfigMap:

```bash
kubectl get cm kube-proxy -n kube-system -o yaml | grep mode
```

## Seeing the rules

```bash
# the chain for one Service, iptables mode
iptables -t nat -L KUBE-SERVICES -n | grep <cluster-ip>
iptables -t nat -L KUBE-SVC-XXXX -n         # the per-Service chain: one jump per endpoint, with probabilities
iptables -t nat -L KUBE-SEP-XXXX -n         # a single endpoint: DNAT to the Pod IP

# IPVS mode
ipvsadm -Ln
```

You do not need to memorise the chain names; you need to know that when a
Service "does not work" and the endpoints look right, the next question is
whether these rules exist on the node where the client Pod runs.

## How it runs, and how it breaks

```bash
kubectl get ds -n kube-system kube-proxy
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide   # one per node, all Running?
kubectl describe ds -n kube-system kube-proxy | grep -A3 "Args\|Mounts"
```

Symptoms of a broken kube-proxy:

- Pods can reach each other **by IP** but not through a **Service IP**;
- `nslookup` resolves the Service name fine (DNS is CoreDNS, not kube-proxy)
  but connecting to it hangs;
- only the Pods on one node are affected (kube-proxy is per node).

Exam-style faults: the DaemonSet's container references a config file path
that does not match the ConfigMap mount (`--config=/var/lib/kube-proxy/...`),
or the ConfigMap name was changed. `kubectl logs` on the kube-proxy Pod names
the missing file.

:::exam-tip
Service problems split cleanly: **name does not resolve** → CoreDNS.
**Resolves but cannot connect** → endpoints (selector/ports) first, then
kube-proxy on the client's node. Keep the two apart and you halve the search.
:::

## What kube-proxy is not

It is not in the data path for Pod-to-Pod traffic - the CNI plugin handles
that. It does not do DNS. And it is not the Ingress controller - kube-proxy
stops at Services; Ingress is another layer on top.

:::note
Some CNI plugins (Cilium, for example) can replace kube-proxy entirely with
their own eBPF implementation. On such a cluster there is no kube-proxy
DaemonSet and that is fine - check before you "fix" it.
:::

## Check yourself

1. Where does a ClusterIP "live", and who makes packets to it go anywhere?
2. A Pod can `curl` another Pod's IP but not the Service in front of it, and
   DNS resolves correctly. Which component, on which node, do you look at?
3. How do you find out whether kube-proxy is running in iptables or IPVS mode?
