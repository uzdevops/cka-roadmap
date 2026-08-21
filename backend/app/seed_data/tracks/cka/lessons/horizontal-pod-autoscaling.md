## More replicas when it is busy

The HorizontalPodAutoscaler watches a metric on the Pods of a Deployment (or
ReplicaSet, StatefulSet) and writes `spec.replicas` to keep the metric near a
target, between a minimum and a maximum.

```bash
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10
kubectl get hpa
# NAME         REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# php-apache   Deployment/php-apache   12%/50%   1         10        1          30s
```

`12%/50%` is current versus target: average CPU usage across the Pods, as a
percentage of their CPU **request**. That is why the Pods must have requests;
without them the HPA cannot compute a percentage and shows `<unknown>`.

## The object

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization       # percent of request
          averageUtilization: 50
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue      # an absolute amount per Pod
          averageValue: 500Mi
  behavior:                       # optional: how fast it may move
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Pods
          value: 4
          periodSeconds: 15
```

`autoscaling/v2` is the version to write: it supports several metrics (the
HPA takes the **largest** resulting replica count), memory, custom metrics
(`type: Pods`, `type: Object`) and external ones (`type: External`), and the
`behavior` block. `autoscaling/v1` is CPU-only; `kubectl autoscale` creates
that, and it is fine for the exam.

## The algorithm

```
desiredReplicas = ceil( currentReplicas * currentMetric / targetMetric )
```

Two Pods averaging 80 % against a 50 % target: `ceil(2 * 80/50) = 4`. It
re-evaluates every 15 seconds, ignores changes within a 10 % tolerance, and
by default waits 5 minutes of sustained lower load before scaling **down**
(`stabilizationWindowSeconds`) - so scale-up is quick, scale-down is
cautious, which is what you want.

## Watching it work

```bash
kubectl run load --rm -it --image=busybox:1.36 --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://php-apache; done"
# in another terminal
kubectl get hpa php-apache -w
# php-apache   Deployment/php-apache   250%/50%   1   10   1
# php-apache   Deployment/php-apache   250%/50%   1   10   4
# php-apache   Deployment/php-apache    48%/50%   1   10   5
kubectl get deployment php-apache       # REPLICAS follows
kubectl describe hpa php-apache         # Events: SuccessfulRescale ... New size: 4; reason: cpu resource utilization above target
```

Stop the load and, five minutes later, it walks back down to 1.

## What goes wrong

| Symptom | Cause |
|---|---|
| TARGETS `<unknown>/50%` | Metrics Server not running, or the Pods have no CPU `requests` |
| `FailedGetResourceMetric` in describe | same two causes, spelled out |
| never scales above N | `maxReplicas`, or the Deployment cannot schedule more Pods (no room - that is the Cluster Autoscaler's job) |
| flaps up and down | target too tight, or the app's CPU is spiky - widen `behavior` windows |
| replicas reset on every `kubectl apply` | your Deployment file has `replicas: 1`; remove `replicas` from the file when an HPA owns it |

:::exam-tip
`kubectl autoscale deployment X --cpu-percent=50 --min=2 --max=8` is the
whole answer to a typical task. If the task mentions memory or a second
metric, you need the `autoscaling/v2` manifest - `kubectl autoscale ... $do`
gives you a v1 skeleton to upgrade.
:::

## Check yourself

1. Three Pods average 90 % CPU against a 60 % target. How many replicas does
   the HPA ask for?
2. Why does an HPA need the Pods to set CPU requests?
3. You `kubectl apply` the Deployment and the HPA's scaling is undone. Why,
   and what do you change in the file?
