## Reading a version number

```
v1.30.2
 │  │ └── patch: bug and security fixes, no new features
 │  └──── minor: a new release about three times a year - features, deprecations, API changes
 └─────── major: has been 1 since 2015
```

```bash
kubectl version            # client and server
kubectl get nodes          # the kubelet version on each node, in the VERSION column
kubeadm version
```

Every control plane component - `kube-apiserver`, `kube-controller-manager`,
`kube-scheduler`, `kubelet`, `kube-proxy`, `kubectl` - ships at the same
version from the same release. etcd and CoreDNS have their own version
numbers; kubeadm pins which ones it deploys with each Kubernetes release.

## How long a minor is supported

The three most recent minors get patch releases (roughly **14 months** of
support per minor). Run something older and there are no security patches -
so "upgrade one minor at a time, every few months" is the rhythm a cluster
needs to stay on a supported line.

## Version skew: who may be newer than whom

Not everything has to be on the same version at the same moment - if it did,
an upgrade would be impossible. The rules:

| Component | May be | Relative to kube-apiserver |
|---|---|---|
| **kube-apiserver** (several, in HA) | n, n-1 | the newest API server defines n |
| **kubelet** | n ... n-3 | never newer than the API server |
| **kube-proxy** | n ... n-3 | same as kubelet |
| **kube-controller-manager, kube-scheduler** | n, n-1 | never newer |
| **kubectl** | n+1, n, n-1 | one minor either way |

In words: the API server goes first, and everything else follows but may
lag. The kubelet may be up to three minors behind, which is what lets you
upgrade the control plane and then the workers one by one over days if you
want.

:::exam-tip
Two numbers to remember under pressure: **one minor at a time** for the
upgrade itself (1.29 → 1.30 → 1.31, never 1.29 → 1.31), and the **API server
first**. Everything in the next lessons follows from those two.
:::

## Where the binaries come from

| | |
|---|---|
| Source and release notes | github.com/kubernetes/kubernetes/releases |
| kubeadm, kubelet, kubectl packages | the `pkgs.k8s.io` apt/yum repositories, one repo **per minor** (`/v1.30/`) |
| Container images for the control plane | `registry.k8s.io/kube-apiserver:v1.30.2` etc. |

```bash
apt-cache madison kubeadm | head -5       # which versions the configured repo offers
```

That "one repo per minor" point matters: to upgrade from 1.30 to 1.31 you
first point the package repository at `/v1.31/`, then `apt-get update`, and
only then does `kubeadm=1.31.x` become installable. Forgetting the repo switch
is the most common reason "the new version is not available".

## Deprecations

A minor release can deprecate an API version and a later one removes it
(`extensions/v1beta1` Ingress, `PodSecurityPolicy`, the `batch/v1beta1`
CronJob). Manifests using a removed version fail to apply after the upgrade.
`kubectl api-resources` and the release notes tell you what is going; the
`kubectl convert` plugin rewrites old manifests. Before a minor upgrade, it
is worth one search of your manifests for versions the release notes name.

## Check yourself

1. What changes in a patch release, and what may change in a minor?
2. The API server is at 1.30. What is the oldest kubelet version allowed in
   the cluster?
3. You want to go from 1.29 to 1.31. How many upgrades is that, and what do
   you change before each one so the packages can be found?
