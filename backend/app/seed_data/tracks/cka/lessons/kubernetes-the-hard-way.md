## The tutorial that makes everything else obvious

"Kubernetes the Hard Way" is Kelsey Hightower's walkthrough of building a
cluster **without** kubeadm - no installer, no distribution. You generate
every certificate with a CA you made, write every kubeconfig by hand,
configure etcd, the API server, controller manager and scheduler as systemd
services with every flag spelled out, set up the kubelets and kube-proxy on
the workers, wire the Pod network with routes, and deploy CoreDNS yourself.

github.com/kelseyhightower/kubernetes-the-hard-way - originally for GCP,
now written for a few local VMs, kept current with recent Kubernetes
versions.

## Why do it once

Everything kubeadm hides is something the exam can break:

| You do by hand in KTHW | Which makes this exam task obvious |
|---|---|
| generate the CA and every component's cert with `cfssl`/`openssl`, setting CN and O | why `CN=system:node:node01, O=system:nodes`; reading a cert to find who it is |
| write `kubelet.kubeconfig`, `kube-proxy.kubeconfig`, `admin.kubeconfig` | what a kubeconfig is made of; fixing a broken one |
| start `kube-apiserver` as a systemd unit with 30 flags | what each `--etcd-*`, `--client-ca-file`, `--service-cluster-ip-range` flag does, and what a typo does |
| configure etcd with `--initial-cluster`, peer and client certs | etcd's two ports, two CAs, and the backup command's flags |
| write static routes between nodes for the Pod CIDRs | what a CNI plugin is actually doing for you |
| deploy CoreDNS from a manifest | the Corefile and the kube-dns Service |
| bootstrap kubelets and approve their CSRs | the Certificates API, `kubectl certificate approve` |

A kubeadm cluster is exactly this, with the flags in static Pod manifests
instead of systemd units and the certificates generated for you. When a
task breaks one of those flags, someone who has typed them all once sees the
fault in seconds.

## How it differs from what you will run

| KTHW | kubeadm |
|---|---|
| control plane as systemd services | control plane as static Pods under the kubelet |
| certs in `/var/lib/kubernetes` | certs in `/etc/kubernetes/pki` |
| routes by hand | a CNI plugin |
| no upgrade story | `kubeadm upgrade` |

So the **concepts** transfer one to one, and the **paths** do not. Do not
memorise KTHW's file locations for the exam; memorise kubeadm's.

:::tip
Budget a day for it, with three VMs. Do not automate it the first time -
the point is typing the flags. The second time, if there is one, is when a
script is allowed.
:::

## The curriculum's position

The 2025 CKA curriculum says "prepare underlying infrastructure for
installing a Kubernetes cluster" and "create and manage Kubernetes clusters
using kubeadm" - not "by hand". KTHW is how you earn the understanding; the
next three lessons and the lab are the kubeadm skill the exam grades.

## Check yourself

1. Name three things kubeadm does for you that KTHW makes you do by hand.
2. In a KTHW cluster, what supervises the API server, and in a kubeadm
   cluster?
3. Which exam task does "write the kube-apiserver systemd unit by hand"
   prepare you for?
