## Mock exam 2

Two hours. Ten tasks. Total weight 100. Harder than mock 1: fewer
one-liners, more YAML, two tasks that need a node. Verify every end state.

```bash
alias k=kubectl; export do="--dry-run=client -o yaml"
```

---

**1.** (12) Take a snapshot of the etcd database and save it to
`/opt/etcd-backup.db`. (Use the certificates from the etcd static Pod's
manifest.)

**2.** (8) Create a Pod named `redis-storage` using the image
`redis:alpine` with a volume of type `emptyDir` named `redis-storage`
mounted at `/data/redis`.

**3.** (8) Create a Pod named `super-user-pod` using the image
`busybox:1.28`, running `sleep 4800`, with the `SYS_TIME` capability added
to its container.

**4.** (10) A PersistentVolumeClaim named `my-pvc` exists (create it first:
a 10Mi RWO PVC, and a matching hostPath PV `pv-1` at `/tmp/pv1`). Create a
Pod named `use-pv` using the image `nginx` that mounts the claim at
`/data`.

**5.** (10) Create a Deployment named `nginx-deploy` using the image
`nginx:1.16` with `1` replica. Then upgrade it to `nginx:1.17` using a
rolling update, and record the change cause as `nginx 1.17`.

**6.** (14) Create a user `john` for the `development` namespace: generate a
private key and CSR, submit a CertificateSigningRequest named
`john-developer` with `system:authenticated` group and signer
`kubernetes.io/kube-apiserver-client`, approve it, create a Role
`developer` in `development` allowing `create, list, get, update, delete`
on `pods`, and bind it to `john` with a RoleBinding `john-developer`.
Verify with `kubectl auth can-i`.

**7.** (12) Create an `nginx` Pod named `nginx-resolver` and expose it
internally with a Service `nginx-resolver-service`. Test that the Service
and the Pod are resolvable from a `busybox:1.28` Pod; record the Service
lookup in `/root/CKA/nginx.svc` and the Pod lookup in
`/root/CKA/nginx.pod`.

**8.** (10) Create a static Pod named `nginx-critical` on the worker node
`node01` using the `nginx` image. Ensure it is recreated if deleted.

**9.** (8) A Deployment `api` in namespace `backend` must run exactly one
Pod per node, including control-plane nodes. Convert it to the right
workload type with the same Pod template (image `nginx:alpine`, label
`app=api`). (Create the Deployment first with 1 replica.)

**10.** (8) Create a ConfigMap `app-config` with `LOG_LEVEL=debug` and
`MODE=test`, and a Pod `cm-pod` (image `busybox:1.28`, command `env;
sleep 3600`) that loads **all** keys of the ConfigMap as environment
variables. Verify with `kubectl logs`.

---

Score, then solutions.

:::exam-tip
Tasks 1, 6 and 7 are the ones that eat time if you have not practised
them. Each is a documentation page you should be able to find in under
thirty seconds: "Operating etcd clusters" (backup), "Certificate Signing
Requests" (user john), "DNS for Services and Pods" (resolver). Know the
search terms.
:::

## Check yourself

1. Which of the ten tasks needed an `ssh`, and did you remember to `exit`?
2. For task 6, which command proved that john can create Pods in
   `development` and cannot in `default`?
3. Which task's docs page took longest to find, and what search term would
   have found it faster?
