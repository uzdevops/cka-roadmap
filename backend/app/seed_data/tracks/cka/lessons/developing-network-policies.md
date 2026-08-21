## Working a real requirement into YAML

The requirement: *the `internal` Pod may talk only to `mysql` on 3306 and to
`payroll` on 8080. Nothing else in, nothing else out, except DNS.* This is
the shape of nearly every NetworkPolicy task; work it in four steps.

### 1. What is the policy about, and which directions?

It protects Pods labelled `name: internal`. It restricts what they **send**
(egress) and - "nothing else in" - what they **receive** (ingress). So:

```yaml
podSelector:
  matchLabels:
    name: internal
policyTypes:
  - Ingress
  - Egress
```

With no `ingress:` rules listed, Ingress is **fully denied** for `internal` -
which is what "nothing else in" asked for. (If `internal` should still be
reachable by, say, a front end on 8080, that is one more `ingress` rule.)

### 2. Find the labels you will match on

```bash
kubectl get pods --show-labels
# internal   name=internal
# mysql      name=mysql
# payroll    name=payroll
kubectl describe pod mysql | grep -i "labels" -A2
```

Match on what is there. Policies match **Pod** labels - not the Service's
name, not the Service's labels. If the task only names Services, look up
their selectors: `kubectl describe svc mysql | grep Selector`.

### 3. Write one egress rule per destination

```yaml
egress:
  - to:
      - podSelector:
          matchLabels:
            name: mysql
    ports:
      - protocol: TCP
        port: 3306
  - to:
      - podSelector:
          matchLabels:
            name: payroll
    ports:
      - protocol: TCP
        port: 8080
```

Each `- to:` entry pairs *its* destinations with *its* ports. Putting both
Pods in one `to:` with both ports would allow `mysql:8080` and
`payroll:3306` as well - harmless here, wrong in principle, and a marker may
test it.

### 4. DNS, or nothing works

```yaml
  - ports:
      - protocol: UDP
        port: 53
      - protocol: TCP
        port: 53
```

A rule with `ports` and **no `to:`** means "to anywhere, on these ports" -
the cleanest DNS allowance. (Some graders want the rule scoped to
`kube-system`; then add `to: [{namespaceSelector: {matchLabels:
{kubernetes.io/metadata.name: kube-system}}}]`.)

### The whole thing

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: internal-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      name: internal
  policyTypes:
    - Egress
    - Ingress
  egress:
    - to:
        - podSelector:
            matchLabels:
              name: mysql
      ports:
        - protocol: TCP
          port: 3306
    - to:
        - podSelector:
            matchLabels:
              name: payroll
      ports:
        - protocol: TCP
          port: 8080
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

```bash
kubectl apply -f internal-policy.yaml
kubectl describe netpol internal-policy
kubectl exec internal -- nc -zv -w 2 mysql 3306          # open
kubectl exec internal -- nc -zv -w 2 payroll 8080        # open
kubectl exec internal -- nc -zv -w 2 payroll 80          # times out - correct
kubectl exec internal -- nslookup payroll                 # works - DNS allowed
```

:::exam-tip
Build it in this order every time: `podSelector` → `policyTypes` → one rule
per (destination, port) → DNS. Then `kubectl describe netpol` and read it
back in English. The two errors that survive to grading: `podSelector` set to
the *destination's* labels instead of the protected Pod's, and a missing
dash that turned two OR'd sources into one AND'd one.
:::

## Variations you will meet

| Requirement | Change |
|---|---|
| "only from the `api` Pods **in the `prod` namespace**" | one `from` item with both `podSelector` and `namespaceSelector` (AND) |
| "from anything in namespace `monitoring`" | `namespaceSelector` alone; label the namespace if it has no label |
| "from an external IP range" | `ipBlock: {cidr: 10.0.0.0/8}` |
| "deny everything to these Pods" | select them, `policyTypes: [Ingress, Egress]`, no rules (plus DNS egress if they must resolve) |
| "allow all ingress to web Pods" | `ingress: [{}]` |

```bash
kubectl label namespace monitoring team=monitoring
kubectl get ns --show-labels     # every namespace has kubernetes.io/metadata.name=<name> automatically
```

That automatic `kubernetes.io/metadata.name` label is the easiest way to
select a namespace by name without labelling anything.

## Check yourself

1. Why must each egress destination get its own `- to:` entry with its own
   `ports`?
2. Write the egress rule that allows DNS to anywhere.
3. A policy "does nothing" on a cluster - what about the CNI do you check
   first?
