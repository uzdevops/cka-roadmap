## The last gate before etcd

A request that reaches the API server is authenticated (who are you),
authorised (may you), and then **admitted**: a chain of plugins gets to look
at the object and either change it or refuse it, before it is validated and
stored. Authorisation answers "may this user create Pods"; admission answers
"may *this* Pod, as written, exist" - and can say "yes, but with these
changes".

```
request ─▶ authN ─▶ authZ ─▶ mutating admission ─▶ schema validation ─▶ validating admission ─▶ etcd
```

Two kinds of plugin, run in that order:

- **Mutating** plugins may alter the object - add a default, inject a
  sidecar, set a field.
- **Validating** plugins may only accept or reject.

Some built-in plugins do both.

## Built-in plugins you will meet

| Plugin | Does |
|---|---|
| `NamespaceLifecycle` | refuses objects in a namespace that does not exist or is terminating (on by default - it is why `kubectl run x -n nope` fails) |
| `LimitRanger` | applies LimitRange defaults and caps |
| `ResourceQuota` | enforces ResourceQuotas |
| `ServiceAccount` | injects the default service account and its token into Pods |
| `DefaultStorageClass` | gives a PVC with no class the default one |
| `NodeRestriction` | stops a kubelet from modifying objects of other nodes - on by default in kubeadm |
| `NamespaceAutoProvision` | creates a namespace that does not exist yet instead of refusing (off by default) |
| `AlwaysPullImages` | forces `imagePullPolicy: Always` |
| `MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook` | call out to your own webhooks - next lesson |

```bash
kube-apiserver -h | grep enable-admission-plugins    # the default list, in the help text
```

## Turning plugins on and off

Admission plugins are **flags on the API server**:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
- --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
- --disable-admission-plugins=DefaultStorageClass
```

`--enable-admission-plugins` *adds to* the default set; it does not replace it.
Save the manifest, wait for the kubelet to restart the API server, confirm:

```bash
ps -ef | grep kube-apiserver | grep -o -- '--enable-admission-plugins=[^ ]*'
kubectl exec -n kube-system kube-apiserver-controlplane -- kube-apiserver -h | grep enable-admission-plugins
```

:::exam-tip
Editing the API server manifest means kubectl is **down** for the 20-40
seconds the API server takes to restart. Do not panic, do not re-edit; wait.
If it does not come back, `crictl ps -a | grep apiserver` and `crictl logs`
on the node - a typo in the plugin name (`NamespaceAutoProvisioning` with an
extra -ing is the classic) is reported there.
:::

## Seeing admission act

```bash
# NamespaceLifecycle (default)
kubectl run nginx --image=nginx -n blue
# Error: namespaces "blue" not found

# enable NamespaceAutoProvision, then:
kubectl run nginx --image=nginx -n blue       # works
kubectl get ns blue                           # it was created for you

# disable DefaultStorageClass, then a new PVC without storageClassName:
kubectl get pvc                               # STORAGECLASS column empty, stays Pending
```

## What admission is not for

It does not decide *who* may do things - that is RBAC. A user who is denied
by RBAC never reaches admission; a user who passes RBAC can still be refused
by a validating plugin because of *what* they sent. Keep the two ideas apart
when a task says "user X may create Pods but not privileged ones" - the first
half is RBAC, the second is admission (a Pod Security admission level on the
namespace, or a validating webhook).

:::note
Pod Security Admission - the built-in replacement for PodSecurityPolicy -
is itself an admission plugin (`PodSecurity`), configured per namespace with
labels such as `pod-security.kubernetes.io/enforce: restricted`. It is on by
default and is the modern answer to "no privileged Pods in this namespace".
:::

## Check yourself

1. In the request pipeline, does admission run before or after
   authorization, and why does the order matter?
2. How do you enable `NamespaceAutoProvision`, and what happens to kubectl
   while you do?
3. `kubectl run x --image=nginx -n doesnotexist` fails on a default cluster.
   Which plugin refused it?
