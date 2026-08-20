## Getting outside traffic in, the cloud way

A NodePort gives the world a port on every node - but "every node" is a list
of IPs that changes, and port 31234 is not what a customer types. In a cloud,
the fix is a `type: LoadBalancer` Service: Kubernetes asks the cloud for a real
load balancer, the cloud hands back an external IP or hostname, and traffic
to it is spread across the NodePorts.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl get svc web
# NAME   TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
# web    LoadBalancer   10.96.33.12    203.0.113.45     80:31907/TCP   40s
```

Look at the row: a ClusterIP, a NodePort (`31907`), and an EXTERNAL-IP. The
three types really do nest. A LoadBalancer Service **is** a NodePort Service
that additionally asks a **cloud controller** to provision something in front.

## Who provisions it

The **cloud-controller-manager** - a control plane component that is present
only on cloud-integrated clusters (EKS, GKE, AKS, and on-prem setups with a
cloud provider plugin). It watches LoadBalancer Services and calls the cloud
API.

Which is why, on a bare cluster (kind, minikube, kubeadm on plain VMs), this
happens:

```bash
kubectl get svc web
# NAME   TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
# web    LoadBalancer   10.96.33.12   <pending>     80:31907/TCP   5m
```

`<pending>` forever is not an error. Nothing exists to fulfil the request.
The NodePort part works exactly as before; only the external IP never comes.

:::exam-tip
The exam clusters have no cloud provider. If a task says "expose as
LoadBalancer", create it and move on - `<pending>` is the correct final state
and you are graded on the Service object, not on an IP appearing.
:::

## Filling the gap on-prem

Two common answers when you want LoadBalancer Services without a cloud:

- **MetalLB** - a controller that hands out IPs from a range you give it and
  announces them with ARP or BGP. From the Service's point of view it is
  indistinguishable from a cloud.
- **An Ingress / Gateway** in front of ClusterIP Services - one entry point for
  many HTTP applications, which is usually what you wanted anyway. That is the
  networking phase's Ingress and Gateway API lessons.

## A few fields worth knowing

```yaml
spec:
  type: LoadBalancer
  loadBalancerIP: 203.0.113.45          # ask for a specific IP (cloud/MetalLB dependent)
  externalTrafficPolicy: Local          # only route to Pods on the node that received the packet
  loadBalancerSourceRanges:
    - 198.51.100.0/24                   # allow-list at the load balancer
```

`externalTrafficPolicy: Local` preserves the client's source IP and avoids an
extra hop, at the cost of uneven load if Pods are not spread evenly; the
default `Cluster` does the opposite trade.

## Choosing between the three

| You want | Use |
|---|---|
| internal only | ClusterIP |
| quick external access for a test, or a port behind your own LB | NodePort |
| a real public endpoint on a cloud | LoadBalancer |
| many HTTP apps behind one public endpoint | Ingress or Gateway over ClusterIPs |

## Check yourself

1. What does a LoadBalancer Service contain that a NodePort does not, and
   which component provides it?
2. `EXTERNAL-IP` shows `<pending>` on the exam cluster. What do you do?
3. What does `externalTrafficPolicy: Local` buy you, and what does it cost?
