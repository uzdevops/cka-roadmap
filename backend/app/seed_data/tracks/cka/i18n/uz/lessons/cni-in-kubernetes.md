## Plugin’ni kim va nima bilan chaqiradi

Har bir node’da CNI’ni chaqiruvchi - **konteyner runtime**’i, ya’ni
containerd. Kubelet containerd’dan Pod sandbox so’raydi; containerd tarmoq
namespace’ini yaratadi va uning uchun CNI plugin’ni chaqiradi; plugin IP’ni
qaytaradi; containerd buni kubelet’ga yetkazadi; kubelet esa
`status.podIP`’ni yozadi.

```
kubelet ──CRI──▶ containerd ──CNI (exec)──▶ /opt/cni/bin/<type>  ADD/DEL
                                 ▲
              /etc/cni/net.d/*.conflist   (qaysi plugin, qanday config)
```

Node’da ikkita katalog bor va ikkalasi ham **containerd**’da sozlanadi
(kubelet’ning eski `--network-plugin=cni`, `--cni-conf-dir` va
`--cni-bin-dir` flag’lari dockershim olib tashlanganidan beri yo’q):

```bash
grep -A4 '\[plugins."io.containerd.grpc.v1.cri".cni\]' /etc/containerd/config.toml
#   bin_dir = "/opt/cni/bin"
#   conf_dir = "/etc/cni/net.d"
```

```bash
ls /opt/cni/bin            # plugin binary'lari
ls /etc/cni/net.d          # konfiguratsiya; saralashda birinchi turgan fayl yutadi
cat /etc/cni/net.d/10-flannel.conflist
```

```json
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {"type": "flannel", "delegate": {"hairpinMode": true, "isDefaultGateway": true}},
    {"type": "portmap", "capabilities": {"portMappings": true}}
  ]
}
```

`.conflist` - bu **zanjir**: `flannel` interfeys va IP’ni sozlaydi (buni
node’ning subnet’i bilan `bridge` va `host-local` reference plugin’lariga
topshiradi), keyin `portmap` `hostPort`’ni ishlatadigan iptables qoidalarini
qo’shadi. `DEL`’da zanjir teskari tartibda ishlaydi.

## CNI DaemonSet’i nima qiladi

Flannel yoki Calico’ni o’rnatish - bu `kubectl apply -f <manifest>`, u
DaemonSet yaratadi. Har bir node’da uning Pod’i:

1. plugin binary’sini `/opt/cni/bin`’ga nusxalaydi (hostPath mount’dan);
2. config faylni `/etc/cni/net.d`’ga yozadi (ConfigMap’dan);
3. node darajasidagi qismni sozlaydi - `node.spec.podCIDR`’ni o’qiydi,
   overlay qurilmasini yaratadi yoki marshrutlarni o’rnatadi, BGP agentini
   ishga tushiradi;
4. node’lar qo’shilib-chiqib turganda marshrutlarni saqlab turadigan agent
   sifatida ishlashda davom etadi.

Shuning uchun ham o’sha DaemonSet’ning Pod’i node’da Running bo’lmagunicha,
node `NotReady` bo’lib turadi
(`container runtime network not ready: cni plugin not
initialized`) - va shuning uchun DaemonSet’ning Pod’ining o’zi `hostNetwork:
true` ishlatishi va har qanday taint’ga chidashi shart: u hali o’zi qurmagan
Pod tarmog’idan foydalana olmaydi.

```bash
kubectl get ds -A | grep -iE "flannel|calico|weave|cilium"
kubectl get pods -n kube-flannel -o wide                # har bir node'da bittadan, hammasi Running'mi?
kubectl describe node node01 | grep -i "network"       # bor bo'lsa, NotReady sababi
journalctl -u kubelet | grep -i cni | tail
```

## Bo’sh klasterga CNI o’rnatish

```bash
kubectl get nodes               # kubeadm init dan keyin hammasi NotReady - shunday bo'lishi kerak
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
# pod CIDR'ingiz 10.244.0.0/16 bo'lmasa, avval ConfigMap'dagi net-conf.json faylini tahrirlang
kubectl get pods -n kube-flannel -w
kubectl get nodes               # har bir node'da DaemonSet Pod'i ko'tarilishi bilan Ready
```

Calico uchun: `kubectl apply -f .../tigera-operator.yaml`, keyin
`spec.calicoNetwork.ipPools[0].cidr` sizning Pod CIDR’ingizga teng bo’lgan
`custom-resources.yaml`. Weave uchun:
`kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml`
va CIDR’ingiz boshqacha bo’lsa, `IPALLOC_RANGE`’ni sozlab qo’ying.

:::exam-tip
O’rnatish topshirig’i node’larning Ready bo’lishi va Pod’larning IP olishi
bo’yicha baholanadi. Buni buzadigan narsa - CNI’da sozlangan CIDR
klasterning `--pod-network-cidr` iga mos kelmasligi.
Avval `kubectl cluster-info dump | grep
cluster-cidr` ni ishlating, keyin apply qilishdan oldin manifestni unga
moslashtiring. Va agar imtihon manifest faylni mahalliy bersa, o’shani
ishlating - imtihon mashinasida internet yo’q.
:::

## O’zingizni tekshiring

1. Yangi Pod uchun CNI plugin’ni qaysi komponent chaqiradi va u plugin’ni
   hamda uning config’ini qayerdan topadi?
2. Nega CNI DaemonSet’ining Pod’i `hostNetwork: true` ishlatishi shart?
3. Node "cni plugin not initialized" bilan NotReady bo’lib qoldi. Qaysi ikki
   narsani tekshirasiz?
