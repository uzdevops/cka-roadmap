## Two checklists you can run without thinking

The previous lessons explained *why*. This one is the *what*: two
ordered checklists, for "cannot connect" and "will not mount", to run top
to bottom until one line is the answer.

## Checklist A - connectivity

Symptom: something cannot reach something. Name the two ends and the
path, then check each hop.

```
 client Pod ──(DNS)──▶ Service name ──▶ ClusterIP ──(kube-proxy)──▶ Endpoints ──(CNI)──▶ server Pod:port ──▶ process listening
```

| # | Check | Command | If it fails |
|---|---|---|---|
| 1 | server Pod Running and **Ready** | `kubectl get pod <p> -n <ns>` | the app layer (status, probes, logs) |
| 2 | the process **listens** on the port | `kubectl exec <p> -- ss -lntp` or `netstat -lntp`, or `curl localhost:<port>` from inside | wrong `containerPort`/app config; the app binds `127.0.0.1` instead of `0.0.0.0` |
| 3 | Pod IP reachable from another Pod | `kubectl exec <client> -- curl -m3 <pod-ip>:<port>` | CNI, or a **NetworkPolicy** (`kubectl get netpol -n <ns>`; `describe`) |
| 4 | Service has **Endpoints** | `kubectl get ep <svc> -n <ns>` | selector ≠ Pod labels, or Pods not Ready, or wrong namespace |
| 5 | Service ports map | `kubectl describe svc <svc>`: `Port` → `TargetPort` = container's port; named port exists | fix `targetPort` (number or the container's port **name**) |
| 6 | ClusterIP reachable | `curl -m3 <cluster-ip>:<port>` from a Pod | kube-proxy (DaemonSet healthy? config path?) |
| 7 | name resolves | `nslookup <svc>.<ns>.svc.cluster.local` | CoreDNS, `kube-dns` endpoints, Pod `resolv.conf`, NetworkPolicy on udp/53 |
| 8 | cross-namespace name | using `<svc>.<ns>` not just `<svc>` | DNS search domains only cover the Pod's own namespace |
| 9 | NodePort from outside | `curl <node-ip>:<nodePort>`; `kubectl get svc` TYPE NodePort | firewall on the node; wrong node IP; Service type ClusterIP |
| 10 | Ingress | `kubectl describe ingress`; controller Pod logs; backend Service **name and port** match; IngressClass set; host header | Ingress points at a Service/port that does not exist; no controller; missing `ingressClassName` |
| 11 | NetworkPolicy | `kubectl get netpol -A`; does one **select** the server or client Pod? | default-deny without an allow; `policyTypes` includes Egress on the client; ports/protocol mismatch; the DNS egress rule missing |

Useful throwaway clients:

```bash
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -n <ns> -- sh      # wget, nslookup, nc
kubectl run tmp --rm -it --image=nicolaka/netshoot --restart=Never -- bash        # curl, dig, ss, tcpdump
kubectl debug -it <pod> --image=busybox:1.36 --target=<container>                # into a distroless Pod's namespace
```

## Checklist B - storage

Symptom: Pod `Pending` or `ContainerCreating`, or the app says it cannot
write.

```
 Pod volumes: ──▶ PVC ──(bound?)──▶ PV ──(on this node? provisioner?)──▶ mount ──▶ permissions in the container
```

| # | Check | Command | If it fails |
|---|---|---|---|
| 1 | Pod Events | `kubectl describe pod <p>` → `FailedScheduling`, `FailedMount`, `FailedAttachVolume` | the message names the volume and the reason |
| 2 | PVC **Bound**? | `kubectl get pvc -n <ns>` | `Pending`: no PV matches or no provisioner - next rows |
| 3 | PVC ↔ PV match | `kubectl describe pvc`: requested **size ≤** PV size, same **accessModes**, same **storageClassName** (empty vs named is a mismatch), selector labels | fix whichever differs, usually `storageClassName` or size |
| 4 | StorageClass exists, provisioner runs | `kubectl get sc`; the provisioner's Pods | a PVC naming a class with no provisioner waits forever; `WaitForFirstConsumer` is **Pending until a Pod uses it** - normal |
| 5 | PV `Available`, not `Released` | `kubectl get pv` | `Released` PVs are not reusable until `claimRef` is cleared or the PV recreated |
| 6 | Pod references the **right PVC name** | `kubectl get pod -o yaml \| grep -A3 persistentVolumeClaim` | a typo in `claimName` → `persistentvolumeclaim "x" not found` |
| 7 | `hostPath` exists on **that** node | `ssh node; ls <path>`; `type: DirectoryOrCreate` | hostPath is per node - a Pod moved to another node finds nothing |
| 8 | `nodeAffinity` on a local PV | `kubectl describe pv` | the Pod can only run on the named node; scheduler says so in Events |
| 9 | ConfigMap/Secret volume | `kubectl get cm,secret -n <ns>`; the key named in `items` or `subPath` | missing object → `ContainerCreating` with `MountVolume.SetUp failed` |
| 10 | RWO volume already attached elsewhere | `kubectl get pod -A -o wide` for the other user | `Multi-Attach error`: the previous Pod still holds it (node down, Terminating) |
| 11 | permissions inside | `kubectl exec <p> -- ls -ld /data; id` | set `securityContext.fsGroup`, or the image runs as a uid that cannot write |

## Reading the Events

```bash
kubectl get events -n <ns> --sort-by=.lastTimestamp | grep -iE "fail|warn|error"
```

```
Warning  FailedScheduling  pod/web  0/3 nodes are available: pod has unbound immediate PersistentVolumeClaims
Warning  FailedMount       pod/web  MountVolume.SetUp failed for volume "config" : configmap "app-cfg" not found
Warning  FailedAttachVolume pod/web Multi-Attach error for volume "pvc-…" Volume is already used by pod(s) web-old
Warning  ProvisioningFailed pvc/data storageclass.storage.k8s.io "fast" not found
```

Each of these is a row in the checklist; the message tells you which.

:::exam-tip
On the exam, run the checklist in order and stop at the first failure - it
is the answer more often than not. The last step, always: reproduce the
original symptom (`curl` the Service; `kubectl get pod` Running and Ready;
write a file into the volume) so the grader sees the fix, not the
diagnosis.
:::

## Check yourself

1. A client cannot reach a Service by name. Give the order of checks from
   the server Pod outwards.
2. A PVC is Pending with a StorageClass whose binding mode is
   `WaitForFirstConsumer`. Is that a problem?
3. A Pod says `Multi-Attach error`. What does it mean and what do you look
   for?
