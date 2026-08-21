## Teaching the API a new kind

Pods, Deployments, Services - the built-in kinds - are each a resource the
API server stores in etcd and serves under a path, with a controller that
acts on them. A **CustomResourceDefinition** adds a new kind the same way,
without changing the API server: you describe the schema, the API server
starts serving `/apis/<your group>/<version>/...`, and `kubectl` can
create, get and delete objects of it like any other.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: flighttickets.flights.com          # MUST be <plural>.<group>
spec:
  group: flights.com
  scope: Namespaced                         # or Cluster
  names:
    kind: FlightTicket
    singular: flightticket
    plural: flighttickets
    shortNames: [ft]
  versions:
    - name: v1
      served: true
      storage: true                         # exactly one version is the storage version
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                from:   {type: string}
                to:     {type: string}
                number: {type: integer, minimum: 1, maximum: 10}
```

```bash
kubectl apply -f flightticket-crd.yaml
kubectl get crd
kubectl api-resources | grep flight
# flighttickets   ft   flights.com/v1   true   FlightTicket
kubectl explain flightticket.spec           # the schema you wrote, through explain
```

Now the custom object:

```yaml
apiVersion: flights.com/v1
kind: FlightTicket
metadata:
  name: my-flight-ticket
spec:
  from: Tashkent
  to: Istanbul
  number: 2
```

```bash
kubectl apply -f ticket.yaml
kubectl get flighttickets        # or: kubectl get ft
kubectl describe ft my-flight-ticket
```

The schema is enforced: `number: 15` is rejected by the API server with a
validation error, exactly as a bad Pod spec would be.

## What a CRD does not do

Creating the object stores it. **Nothing happens.** No ticket is booked,
because nothing is watching for FlightTickets. A CRD is a data type; the
behaviour comes from a **custom controller** - a program (usually a
Deployment in the cluster) that watches the new kind and acts on each
object, the way the Deployment controller watches Deployments. That is the
next lesson; the lesson after is the **operator** pattern that packages the
two together.

```
CRD (schema) + custom objects (data) + custom controller (behaviour) = an operator
```

## Reading CRDs you did not write

Most clusters carry CRDs from things you installed - cert-manager's
`Certificate`, Prometheus's `ServiceMonitor`, Argo's `Application`, the
Gateway API's `HTTPRoute`. The same commands tell you what they are:

```bash
kubectl get crd
kubectl get crd certificates.cert-manager.io -o yaml | grep -A20 openAPIV3Schema
kubectl explain certificate.spec --recursive
kubectl get certificates -A
```

:::exam-tip
CRD tasks in the exam are "create this CRD from the spec given / create an
object of this custom kind / list the custom objects". The checks: `metadata.name`
is `<plural>.<group>`; `scope` matches the task; exactly one version has
`storage: true`; the object's `apiVersion` is `<group>/<version>`. Then
`kubectl api-resources | grep <group>` proves the API knows it.
:::

## Deleting

```bash
kubectl delete ft my-flight-ticket
kubectl delete crd flighttickets.flights.com      # deletes EVERY FlightTicket object with it
```

Deleting a CRD deletes all its objects. On a cluster where an operator is
using them, that is an outage; uninstall the operator first.

## Check yourself

1. What does creating a CRD give you, and what does it not give you?
2. What must `metadata.name` of a CRD be, and what must one of its versions
   set?
3. You create a custom object and "nothing happens". Is that a bug?
