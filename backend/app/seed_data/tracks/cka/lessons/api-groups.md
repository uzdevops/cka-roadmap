## The vocabulary RBAC is written in

Every RBAC rule says "these **verbs** on these **resources** in this **API
group**". If you do not know which group a resource is in, you cannot write
the rule - and `apiGroups: [""]` versus `apiGroups: ["apps"]` is the
difference between a Role that works and one that silently grants nothing.

```bash
curl -sk https://localhost:6443/ --cert admin.crt --key admin.key --cacert ca.crt
kubectl get --raw / | jq .paths        # the same, through kubectl's credentials
# "/api", "/apis", "/healthz", "/metrics", "/openapi/v2", "/version", ...
```

Two roots matter:

| Path | Called | Holds |
|---|---|---|
| `/api` | the **core** (legacy) group | Pods, Services, Namespaces, Nodes, ConfigMaps, Secrets, PVs, PVCs, ServiceAccounts, Events, Endpoints |
| `/apis` | the **named** groups | everything else |

```
/api/v1/namespaces/default/pods
/apis/apps/v1/namespaces/default/deployments
/apis/batch/v1/namespaces/default/jobs
/apis/networking.k8s.io/v1/namespaces/default/ingresses
/apis/rbac.authorization.k8s.io/v1/clusterroles
/apis/storage.k8s.io/v1/storageclasses
/apis/certificates.k8s.io/v1/certificatesigningrequests
```

The URL *is* the structure: `/apis/<group>/<version>/namespaces/<ns>/<resource>/<name>`,
and for the core group the `<group>` segment is missing - which is why its
apiGroup in RBAC is the empty string.

## The table to have in your head

| Group | In RBAC `apiGroups` | Resources |
|---|---|---|
| core | `""` | pods, services, configmaps, secrets, namespaces, nodes, persistentvolumes, persistentvolumeclaims, serviceaccounts, events, endpoints |
| `apps` | `apps` | deployments, replicasets, daemonsets, statefulsets |
| `batch` | `batch` | jobs, cronjobs |
| `networking.k8s.io` | `networking.k8s.io` | ingresses, networkpolicies, ingressclasses |
| `rbac.authorization.k8s.io` | `rbac.authorization.k8s.io` | roles, rolebindings, clusterroles, clusterrolebindings |
| `storage.k8s.io` | `storage.k8s.io` | storageclasses, volumeattachments |
| `certificates.k8s.io` | `certificates.k8s.io` | certificatesigningrequests |
| `autoscaling` | `autoscaling` | horizontalpodautoscalers |
| `policy` | `policy` | poddisruptionbudgets |
| `apiextensions.k8s.io` | `apiextensions.k8s.io` | customresourcedefinitions |

```bash
kubectl api-resources                       # every resource, its group, short name, namespaced?, kind
kubectl api-resources --namespaced=false    # cluster-scoped only
kubectl api-resources --api-group=apps
kubectl api-versions                        # every group/version the server serves
```

`kubectl api-resources` is the authoritative version of the table for *your*
cluster, CRDs included. Its APIVERSION column is exactly the string that goes
in a manifest's `apiVersion`, and the group part of it is what goes in RBAC.

## Resources, subresources, verbs

A **resource** is the noun (`pods`); a **subresource** is a facet of it
accessed through its own path: `pods/log`, `pods/exec`, `pods/status`,
`deployments/scale`. RBAC names them as `resources: ["pods/log"]` - granting
`get` on `pods` does **not** grant `get` on `pods/log`; `kubectl logs` needs
the subresource.

**Verbs** are the HTTP methods with Kubernetes names:

| Verb | HTTP | kubectl |
|---|---|---|
| `get` | GET one | `get pod x`, `describe` |
| `list` | GET collection | `get pods` |
| `watch` | GET with watch | `get pods -w`, every controller |
| `create` | POST | `create`, `run`, `apply` (new) |
| `update` | PUT | `replace`, `edit` |
| `patch` | PATCH | `patch`, `apply` (existing), `set image`, `scale` |
| `delete` | DELETE | `delete` |
| `deletecollection` | DELETE collection | `delete pods --all` |

:::exam-tip
When a Role "does not work", check three things in order: the `apiGroups`
(`""` for Pods and Services, `apps` for Deployments), the resource **plural
lowercase** name (`deployments`, not `Deployment`), and whether the verb the
user actually needs is `list` (for `get pods`) rather than `get`. `kubectl
auth can-i list pods --as dev-user -n dev` tells you in one line.
:::

## Talking to the API directly

```bash
kubectl proxy &                          # localhost:8001, using your kubeconfig credentials
curl localhost:8001/apis/apps/v1/namespaces/default/deployments | jq '.items[].metadata.name'
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes | jq .
```

`kubectl proxy` is not `kube-proxy`: one is a local HTTP proxy to the API
server for you; the other is the per-node Service router. Same word,
unrelated jobs.

## Check yourself

1. What is the `apiGroups` value for Pods, and for Deployments?
2. A Role grants `get` and `list` on `pods`, but `kubectl logs` is still
   forbidden. Why?
3. Which command lists every resource with its API group for your cluster?
