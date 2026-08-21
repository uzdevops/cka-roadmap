## The default is "everyone talks to everyone"

The Kubernetes network model guarantees that every Pod can reach every other
Pod, in every namespace, without NAT. Convenient, and exactly what you do not
want between a payroll database and a marketing front end. A
**NetworkPolicy** is how you say "only these may talk to those".

Two things before the YAML:

1. A NetworkPolicy **selects Pods**, not Services or nodes, by labels.
2. It is only enforced if the **CNI plugin** supports it. Calico, Cilium,
   Weave: yes. Flannel: **no** - policies are accepted by the API and
   silently do nothing. On a Flannel cluster the answer to "why is my
   NetworkPolicy not working" is "it cannot".

## How selection and direction work

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: prod
spec:
  podSelector:                  # WHICH Pods this policy protects (in this namespace)
    matchLabels:
      role: db
  policyTypes:
    - Ingress                   # this policy has something to say about INCOMING traffic
    - Egress                    # ... and about OUTGOING
  ingress:
    - from:
        - podSelector:          # Pods in THIS namespace with role=api
            matchLabels:
              role: api
      ports:
        - protocol: TCP
          port: 3306
  egress:
    - to:
        - podSelector:
            matchLabels:
              role: backup
      ports:
        - protocol: TCP
          port: 80
```

The rule that makes policies behave: **as soon as any policy selects a Pod
for a direction, that direction becomes default-deny for that Pod, and only
the listed rules open it.** Before the policy, `role: db` Pods accepted
anything; after it, they accept only TCP 3306 from `role: api`, and may only
send to `role: backup` on 80. Pods *not* selected by any policy are
untouched - still wide open.

`policyTypes` is what makes the direction count. A policy with `policyTypes:
[Ingress]` and an `egress:` block ignores the egress block; a policy with
`policyTypes: [Ingress, Egress]` and no `egress:` rules denies **all**
egress. Omit `policyTypes` and it defaults to Ingress, plus Egress if an
`egress` block exists.

:::warning
Policies are **additive** (allow-only). There is no deny rule. Two policies
selecting the same Pod are unioned: anything either one allows is allowed.
To deny, you select the Pod and simply do not allow the thing.
:::

## Responses are fine

Policies are about new connections. If ingress to `db` on 3306 is allowed
from `api`, the replies flow back without an egress rule on `db` - the CNI
tracks the connection. You only need an egress rule when `db` *initiates* a
connection.

## The three selectors in `from` / `to`

| Selector | Matches |
|---|---|
| `podSelector` | Pods by label, in the policy's own namespace |
| `namespaceSelector` | every Pod in namespaces with these labels |
| `ipBlock` | a CIDR (with optional `except`), for things outside the cluster |

```yaml
ingress:
  - from:
      - podSelector:
          matchLabels: {role: api}
        namespaceSelector:              # SAME list item, no dash: AND - api Pods in prod namespaces
          matchLabels: {env: prod}
      - ipBlock:                        # NEW list item, with dash: OR - or this CIDR
          cidr: 192.168.5.10/32
```

That dash is the whole exam question: two selectors in **one** `from` entry
are ANDed; two `from` entries are ORed.

## Common shapes

```yaml
# default deny all ingress in a namespace
spec:
  podSelector: {}
  policyTypes: [Ingress]
---
# default deny all egress (remember DNS!)
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: {}      # any namespace
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
---
# allow everything in (undo a deny for some Pods)
spec:
  podSelector:
    matchLabels: {role: public}
  ingress:
    - {}
```

`podSelector: {}` selects every Pod in the namespace; an empty rule `- {}`
allows from anywhere.

:::exam-tip
Egress policies break DNS first. The moment you write `policyTypes: [Egress]`
the Pod cannot resolve names - nothing you listed allowed port 53. Add the
DNS egress rule above to every egress policy unless the task says otherwise.
:::

## Checking

```bash
kubectl get netpol -n prod
kubectl describe netpol db-policy -n prod          # a readable "Allowing ingress traffic: ... From: ..."
kubectl exec api-pod -- nc -zv db 3306             # should connect
kubectl exec other-pod -- nc -zv db 3306           # should time out
```

`describe` is the sanity check: it prints the policy the way the CNI reads
it, and the AND/OR of your selectors becomes obvious.

## Check yourself

1. After you create a policy selecting `role: db` with only an ingress rule,
   what happens to db's outgoing connections?
2. Write the `from` block for "api Pods in namespaces labelled env=prod" -
   as AND - and the one for "api Pods, OR anything in env=prod namespaces".
3. Your egress policy works for IPs and breaks for names. What did you forget?
