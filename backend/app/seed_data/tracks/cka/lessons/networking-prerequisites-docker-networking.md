## Three networks Docker offers

```bash
docker run --network none nginx      # a namespace with only loopback - no network at all
docker run --network host nginx      # NO separate namespace: shares the host's stack, binds host port 80 directly
docker run nginx                     # the default: bridge
```

| Mode | Namespace | Reachability |
|---|---|---|
| `none` | own, empty | nothing in or out |
| `host` | the host's | everything the host has; port conflicts with the host |
| `bridge` | own, plugged into `docker0` | other containers on the bridge, and out via NAT |

Kubernetes has the same two extremes as Pod fields: `hostNetwork: true` is
`--network host` (used by some CNI and monitoring DaemonSets), and a Pod
with no CNI configured is effectively `none` (stuck in `ContainerCreating`).

## The bridge network, which is last lesson's diagram

```bash
ip link                     # docker0 - a bridge, 172.17.0.1/16, created when Docker starts
docker run -d --name web nginx
docker inspect web --format '{{.NetworkSettings.IPAddress}}'   # 172.17.0.2
ip link                     # a new vethXXXX appeared, master docker0
ip netns                    # Docker hides its namespaces; see below
```

Docker did, for you: create a network namespace, create a veth pair, put one
end in the namespace as `eth0` with 172.17.0.2/16, plug the other into
`docker0`, add a default route in the namespace via 172.17.0.1, and - on
first start - add an iptables MASQUERADE rule for 172.17.0.0/16 so the
container can reach the internet.

```bash
# to see the namespace with ip netns, link it into the expected place
pid=$(docker inspect web --format '{{.State.Pid}}')
mkdir -p /var/run/netns && ln -s /proc/$pid/ns/net /var/run/netns/web
ip netns exec web ip addr            # eth0 172.17.0.2
ip netns exec web ip route           # default via 172.17.0.1
```

## Port mapping

A container on the bridge has a private address nobody outside the host can
reach. `-p` publishes it:

```bash
docker run -d -p 8080:80 nginx
curl http://<host-ip>:8080              # from anywhere that can reach the host
iptables -t nat -L DOCKER -n | grep 8080
# DNAT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80
```

It is an iptables **DNAT** rule: traffic arriving at the host's port 8080 is
rewritten to the container's IP and port. That single rule is the idea behind
a NodePort Service - rewrite traffic arriving at a node port to a Pod behind
it - and kube-proxy is the program that writes those rules for every Service
on every node.

## Where Kubernetes diverges

Docker's bridge is per host: every host has its own 172.17.0.0/16, and
containers on different hosts cannot reach each other without port mapping.
Kubernetes requires that every Pod in the cluster can reach every other Pod
**by its Pod IP**, across nodes, without NAT. That is the extra job a CNI
plugin does beyond what Docker did on one host: give each node a distinct
Pod subnet, and make every node able to route to every other node's subnet
(with routes, or an overlay). Next lesson.

:::tip
`docker network ls` shows `bridge`, `host`, `none` and any user-defined
networks. User-defined bridge networks add DNS between containers by name -
a small preview of what CoreDNS does for Pods.
:::

## Check yourself

1. What does `--network host` change about the container's namespace, and
   what is its Kubernetes equivalent?
2. List the five things Docker does to put a container on the bridge.
3. What iptables rule does `-p 8080:80` create, and which Kubernetes object
   does the same thing?
