## What kubeadm does and does not do

kubeadm is the upstream tool for bootstrapping a cluster with best-practice
defaults. Its scope is deliberately narrow:

| kubeadm does | kubeadm does not |
|---|---|
| preflight-check the node | provision machines |
| generate the CA and all certificates | install a container runtime |
| write kubeconfigs for admin and components | install or configure the CNI |
| write static Pod manifests for etcd, API server, controller manager, scheduler | set up a load balancer for HA |
| start the kubelet with the right config | install a dashboard, metrics, ingress |
| deploy CoreDNS and kube-proxy | manage the OS or packages |
| create bootstrap tokens and the join command | |
| `upgrade` the control plane and kubelet configs | |

Everything in the right column is yours, before or after.

## The order

```
1. every node:       OS prep (swap off, sysctls, modules) -> container runtime -> kubeadm, kubelet, kubectl
2. first control plane:  kubeadm init
3. admin machine:    copy admin.conf -> kubectl works
4. the cluster:      install a CNI  (nodes go Ready)
5. other nodes:      kubeadm join   (workers; --control-plane for more control planes)
6. verify:           kubectl get nodes, get pods -A
```

The CNI step sits between init and join for a reason: nodes are `NotReady`
and CoreDNS stays `Pending` until a network plugin exists; joining workers
before it is allowed but confusing.

## init, in phases

`kubeadm init` runs a list of **phases**, each of which you can run alone
(`kubeadm init phase <name>`) - useful for regenerating one thing later:

```
preflight            checks: 2 CPUs, swap, ports, runtime, unique IDs
certs                CA, apiserver, apiserver-kubelet-client, etcd/*, front-proxy, sa.key
kubeconfig           admin.conf, kubelet.conf, controller-manager.conf, scheduler.conf
kubelet-start        writes /var/lib/kubelet/config.yaml and starts the kubelet
control-plane        static Pod manifests for apiserver, controller-manager, scheduler
etcd                 static Pod manifest for etcd (stacked)
upload-config        stores the config in the kubeadm-config ConfigMap
upload-certs         (with --upload-certs) encrypts certs into a Secret for HA joins
mark-control-plane   labels and taints the node
bootstrap-token      creates a join token and the RBAC for it
kubelet-finalize     rotates the kubelet's cert
addon                deploys CoreDNS and kube-proxy
```

```bash
kubeadm init phase certs apiserver --apiserver-cert-extra-sans=lb.example.com   # regenerate ONE cert
kubeadm init phase upload-certs --upload-certs                                   # a fresh certificate key for joining a control plane
kubeadm config print init-defaults                                                # the config file shape
```

## The flags you actually pass

```bash
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \              # MUST match the CNI you will install
  --apiserver-advertise-address=192.168.1.10 \     # the IP the API server listens on (multi-NIC nodes)
  --control-plane-endpoint=lb.example.com:6443 \   # for HA, or future HA
  --upload-certs                                   # for HA joins
```

Or a config file (`kubeadm init --config kubeadm-config.yaml`), which is the
way to set anything else - kubelet config, API server extra args, an external
etcd, a different service CIDR.

## join

`init` prints it; it expires in 24 hours:

```bash
kubeadm join 192.168.1.10:6443 --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:1234...
```

- `token` - a **bootstrap token**: authenticates the joining node for long
  enough to get its own certificate.
- `discovery-token-ca-cert-hash` - lets the joining node verify it is talking
  to the right cluster (it hashes the CA it is given and compares).

```bash
kubeadm token list
kubeadm token create --print-join-command        # a new token and the full command, any time later
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex   # the hash by hand
```

On the joining node, `join` runs preflight, gets the CA, submits a CSR for
its kubelet (auto-approved via the token), writes `kubelet.conf`, starts the
kubelet. A control plane join (`--control-plane --certificate-key`) also
pulls the shared certificates and writes its own static Pod manifests.

:::exam-tip
Two join-time faults recur: the token **expired** (`kubeadm token create
--print-join-command` on the control plane), and the joining node's kubelet
already has a stale `/etc/kubernetes/kubelet.conf` from a previous attempt
(`kubeadm reset` first). And after `init`, **copy admin.conf** before
anything else - `kubectl` on the control plane does not work until you do.
:::

## reset

```bash
kubeadm reset -f        # undo init/join on THIS node: stops the kubelet's static Pods, removes /etc/kubernetes/* 
rm -rf /etc/cni/net.d $HOME/.kube/config
iptables -F && iptables -t nat -F && iptables -X    # kube-proxy rules linger
```

`reset` is how you retry a failed init or repurpose a node. It does not
remove the node from the cluster's view - `kubectl delete node <name>` from
the control plane does that.

## Check yourself

1. Name three things kubeadm leaves to you, and at which point in the
   workflow each one happens.
2. What are the two values in a join command for, respectively?
3. The join command from yesterday's init fails today. Why, and what do you
   run?
