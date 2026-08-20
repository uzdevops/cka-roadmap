## The default, and the one you use most

A ClusterIP Service is how the parts of an application find each other inside
the cluster: the front end talks to `api`, the API talks to `db`, and none of
them know or care which Pods are behind those names today. It is the default
`type`, so a Service with no `type` at all is a ClusterIP.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl expose deployment api --port=80 --target-port=8080
kubectl get svc api
# NAME   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
# api    ClusterIP   10.96.201.77   <none>        80/TCP    2s
```

## What the IP actually is

The ClusterIP is taken from the **service CIDR** (`--service-cluster-ip-range`
on the API server, `10.96.0.0/12` on a kubeadm default). It is a virtual IP:
no interface has it, nothing pings it. kube-proxy programs every node so that
a packet *to* that IP is rewritten to one of the endpoints. It never changes
for the life of the Service - which is the whole point.

```bash
kubectl get svc -A | head           # kubernetes, kube-dns, and yours - all from the same range
```

:::note
The first address in the range, `10.96.0.1`, is always the `kubernetes`
Service in `default`: the API server itself, exposed to Pods as a ClusterIP.
The `kube-dns` Service is conventionally `10.96.0.10`.
:::

## Reaching it by name

Every Service gets a DNS name from CoreDNS:

```
<service>.<namespace>.svc.cluster.local
```

From a Pod in the **same** namespace the short name works; from another
namespace you need at least `<service>.<namespace>`:

```bash
kubectl run t --rm -it --image=busybox -- sh
/ # wget -qO- api            # same namespace
/ # wget -qO- api.payroll    # Service `api` in namespace `payroll`
/ # nslookup api.payroll.svc.cluster.local
```

## Multiple ports and named ports

```yaml
spec:
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: http       # the name of a containerPort
    - name: metrics
      port: 9090
      targetPort: 9090
```

With more than one port each needs a `name`. A named `targetPort` lets the
Deployment move the container's port without the Service changing.

## Headless: a ClusterIP without the IP

```yaml
spec:
  clusterIP: None
  selector:
    app: db
```

`clusterIP: None` makes a **headless** Service: no virtual IP, no
load-balancing. The DNS name resolves to **the Pod IPs directly**. StatefulSets
use this so each replica gets its own stable name
(`db-0.db.payroll.svc.cluster.local`). If a task says "clients must reach each
Pod individually", this is the answer.

## Without a selector

Leave `selector` out and no endpoints are created automatically - you create
the EndpointSlice (or legacy Endpoints) yourself, pointing at any IPs you
like. That is how a cluster gets a stable internal name for an external
database:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: legacy-db
spec:
  ports:
    - port: 5432
---
apiVersion: v1
kind: Endpoints
metadata:
  name: legacy-db           # same name as the Service
subsets:
  - addresses: [{ip: 192.168.50.20}]
    ports: [{port: 5432}]
```

:::exam-tip
`kubectl expose` builds the selector from the target's labels, which is right
99 % of the time. When it is wrong - the task wants `app=frontend` but the
Deployment's Pods carry `tier=web` - add `--selector=tier=web`, or the Service
will sit there with no endpoints.
:::

## Check yourself

1. Why can you not ping a ClusterIP, and what does that tell you about where
   the "Service" really exists?
2. From a Pod in `default`, what is the shortest name that reaches Service
   `api` in namespace `payroll`?
3. What does `clusterIP: None` change, and which workload relies on it?
