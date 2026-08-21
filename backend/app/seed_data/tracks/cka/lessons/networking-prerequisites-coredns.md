## Running a DNS server by hand

Before meeting CoreDNS as a Deployment in `kube-system`, run it once as a
plain binary, so that the ConfigMap you will later edit is obviously "just
the Corefile".

```bash
wget https://github.com/coredns/coredns/releases/download/v1.11.1/coredns_1.11.1_linux_amd64.tgz
tar -xzf coredns_1.11.1_linux_amd64.tgz
./coredns                      # listens on :53 with no config - answers nothing useful
```

## The Corefile

CoreDNS is configured by one file, a list of **server blocks**, each a zone
and a chain of **plugins**:

```
# Corefile
. {
    hosts /etc/hosts {        # answer from a hosts-format file
        fallthrough           # ...and if the name is not there, continue to the next plugin
    }
    forward . 8.8.8.8         # everything else: ask Google
    log
    errors
}
```

```bash
./coredns -conf Corefile
dig @localhost web            # answered from /etc/hosts
dig @localhost example.com    # forwarded to 8.8.8.8
```

Read a server block as a pipeline: the request for a name in zone `.`
(everything) goes through `hosts`, which answers if it can, falls through
otherwise to `forward`. `log` and `errors` are observability plugins. That
shape - a zone, a chain of plugins, one of which answers - is the whole
model.

## The Corefile Kubernetes ships

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

```
.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

| Plugin | Does |
|---|---|
| `kubernetes cluster.local ...` | **the** plugin: watches Services and Pods through the API and answers `*.cluster.local` |
| `forward . /etc/resolv.conf` | anything not `cluster.local` goes to the node's upstream resolvers |
| `cache 30` | cache answers for 30 s |
| `health`, `ready` | the probes the Deployment uses |
| `reload` | re-read the Corefile when the ConfigMap changes (no restart needed) |
| `loop` | detect a forwarding loop (CoreDNS forwarding to itself) and crash loudly rather than spin |

Every question about "why does CoreDNS resolve X like that" is answered by
one of those lines. Change the ConfigMap, `reload` picks it up within a
minute or two.

## Two edits you may actually make

**Forward a private domain to your own DNS:**

```
corp.internal:53 {
    errors
    cache 30
    forward . 10.10.0.53
}
```

Add it as a second server block in the ConfigMap; now `*.corp.internal`
from any Pod goes to the corporate resolver.

**Rewrite a name** (the `rewrite` plugin): `rewrite name old.example.com
new.example.com` - occasionally the fastest fix when an application has a
hostname baked in.

:::exam-tip
The `forward . /etc/resolv.conf` line is why a Pod can resolve
`google.com`: CoreDNS asks whatever the **node** uses. If external names
fail from Pods but cluster names work, check the nodes' `/etc/resolv.conf` -
and the `loop` plugin in CoreDNS's logs, which names the exact problem when
a node's resolver points back at CoreDNS.
:::

## Check yourself

1. What is a server block, and what does `fallthrough` do inside one?
2. Which plugin answers `api.payroll.svc.cluster.local`, and which answers
   `example.com`?
3. How does a change to the coredns ConfigMap reach the running CoreDNS Pods?
