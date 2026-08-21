## CRD plus controller, packaged

An **operator** is a CRD (or several) and the controller that acts on them,
shipped together as one installable thing, encoding how to run a particular
piece of software. The etcd operator knows how to create an etcd cluster,
add members, take backups and recover from a lost member - because someone
wrote that operational knowledge into the controller. You create one object:

```yaml
apiVersion: etcd.database.coreos.com/v1beta2
kind: EtcdCluster
metadata:
  name: example
spec:
  size: 3
  version: "3.5.12"
```

and the operator does the rest, including the things a human would have done
at 3 a.m.

```
operator = CRDs (the vocabulary) + controller (the runbook, as code) + RBAC + a Deployment to run it
```

That is the whole idea. Prometheus, cert-manager, Strimzi (Kafka), the
PostgreSQL operators, Argo CD - each is an operator: install it, and a new
kind appears that manages something complicated.

## What you actually install

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.0/cert-manager.yaml
kubectl get crd | grep cert-manager         # Certificate, Issuer, ClusterIssuer, ...
kubectl get deploy -n cert-manager          # the controller(s)
kubectl get clusterrole | grep cert-manager # the RBAC it needs to watch its kinds and create Secrets
```

Helm does the same with `helm install`; the **Operator Lifecycle Manager
(OLM)** and **OperatorHub.io** are a catalogue and installer for operators
with upgrade channels. The artefact is the same underneath: CRDs, RBAC, a
Deployment.

## Capability levels

The Operator Framework describes how much an operator does on a scale that
is useful for judging one:

| Level | The operator can |
|---|---|
| 1 - Basic install | deploy the software from its custom resource |
| 2 - Seamless upgrades | upgrade it in place |
| 3 - Full lifecycle | back up, restore, fail over |
| 4 - Deep insights | expose metrics, alerts, log processing |
| 5 - Auto pilot | scale and tune itself |

Most open-source operators are level 2-3. Knowing which level one claims
tells you how much is still your job.

## Why it matters to a cluster administrator

- **You will run many.** Ingress controllers, cert-manager, monitoring,
  storage, service meshes - a modern cluster is an operating system for
  operators.
- **They carry privileges.** An operator's ClusterRole is often broad (it
  must create Secrets, Services, Deployments on your behalf). Read it before
  installing; it is `kubectl get clusterrole <name> -o yaml`.
- **They break in their own way.** A custom object stuck in a pending state
  means the operator's controller is down, lacking permission, or failing -
  its Pod logs, not the object, hold the answer.
- **Upgrades have two halves.** The operator's own version, and the version
  of the thing it manages; read the operator's notes before bumping either.

:::exam-tip
The CKA expects you to know the vocabulary - CRD, custom controller,
operator, OperatorHub - and to do the mechanical part: install from a
manifest, list the CRDs it added, create a custom object, find the
controller's logs. It does not expect you to write one. If a task says
"install the X operator and create a Y", read its manifest for the CRD
kinds first (`kubectl api-resources | grep <group>` after applying) and
then `kubectl explain <kind>` to write the object.
:::

## A minimal checklist for installing one

```bash
# 1. what will it add?
curl -sL <manifest-url> | grep -E "^kind:" | sort | uniq -c
# 2. what may it do?
curl -sL <manifest-url> | grep -A30 "kind: ClusterRole" | head -60
# 3. install, then confirm the pieces
kubectl apply -f <manifest-url>
kubectl get crd,deploy,sa -A | grep <operator-name>
kubectl logs -n <ns> deploy/<operator> | tail
```

## Check yourself

1. Define an operator in one line, in terms of the two lessons before this.
2. You installed an operator and a custom object stays pending. Where do you
   look?
3. Name two reasons to read an operator's ClusterRole before installing it.
