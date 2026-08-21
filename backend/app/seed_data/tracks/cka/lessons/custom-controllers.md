## The loop that makes a resource do something

Every built-in kind has a controller: a process that watches objects of that
kind, compares what they ask for with what exists, and closes the gap. The
ReplicaSet controller sees `replicas: 3` and two Pods, and creates one. A
**custom controller** is the same loop written for your CRD.

```
watch FlightTickets ──▶ for each: is a booking made? ──no──▶ call the airline API, write status
         ▲                                                            │
         └────────────────────────── requeue ◀────────────────────────┘
```

It lives outside the API server - usually as a Deployment in the cluster,
running as a ServiceAccount with RBAC to watch its kind - and talks to the
API server like any other client. Kill it and the objects stay; they just
stop being acted on until it returns.

## The shape of the code

Controllers are written in Go against **client-go**, because that is where
the machinery lives:

- an **informer** keeps a local cache of the objects and fires callbacks on
  add/update/delete - so the controller is not polling the API server;
- a **work queue** collects the keys of objects that need attention;
- a **reconcile** function takes one key, reads the object, reads reality,
  and does whatever makes them match - idempotently, because it will be
  called again.

```go
func (c *Controller) reconcile(key string) error {
    ticket, err := c.lister.FlightTickets(ns).Get(name)
    if errors.IsNotFound(err) { return nil }          // deleted; nothing to do
    if ticket.Status.Booked { return nil }            // already done
    ref, err := airline.Book(ticket.Spec.From, ticket.Spec.To, ticket.Spec.Number)
    if err != nil { return err }                      // error -> requeued with backoff
    ticket.Status.Booked, ticket.Status.Reference = true, ref
    _, err = c.client.FlightsV1().FlightTickets(ns).UpdateStatus(ctx, ticket, metav1.UpdateOptions{})
    return err
}
```

The pattern is the same from the ReplicaSet controller down to the smallest
operator: **level-triggered** (it looks at the current state, not at the
event that woke it), **idempotent** (running twice is safe), **eventually
consistent** (it retries until reality matches).

Frameworks that generate the scaffolding so you write only `reconcile`:
**kubebuilder** and the **Operator SDK** (Go), **Metacontroller** (any
language via webhooks), **kopf** (Python).

## What the administrator needs from this

You will not write a controller in the CKA. You will run clusters full of
them, and the questions that come up are operational:

| Question | Where to look |
|---|---|
| is the controller running? | `kubectl get deploy -n <its namespace>`, its Pod logs |
| why is my custom object not being processed? | controller logs; its RBAC (`auth can-i list <kind> --as system:serviceaccount:<ns>:<sa>`) |
| what has it done? | `kubectl describe <kind> <name>` - good controllers write **status** and **events** |
| is it fighting with something? | an object that keeps changing back - two controllers, or a controller plus a human |

```bash
kubectl logs -n flights deploy/flightticket-controller -f
kubectl describe ft my-flight-ticket | tail      # Status and Events, written by the controller
kubectl get ft my-flight-ticket -o jsonpath='{.status}'
```

:::tip
A controller that writes `status` and `Events` is debuggable; one that does
not is a black box. When you evaluate an operator to install, `kubectl
describe` one of its objects and see whether it tells you anything.
:::

## Status is the controller's half of the object

`spec` is yours - what you want. `status` is the controller's - what it
observed and did. The split is enforced by giving the controller a `status`
subresource (`subresources: {status: {}}` in the CRD) so that it can update
status without racing your edits to spec, and so RBAC can let it write
status but not spec. Every built-in kind works this way; that is why
`kubectl get deploy` shows READY/AVAILABLE columns the controller filled in.

## Check yourself

1. What does a controller do in one sentence, and what happens to existing
   custom objects if it stops?
2. Why must `reconcile` be idempotent?
3. A custom object sits there unprocessed. Name the two first things you
   check.
