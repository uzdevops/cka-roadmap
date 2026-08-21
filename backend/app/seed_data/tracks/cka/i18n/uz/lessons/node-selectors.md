## Node tanlashning eng oddiy yo’li

Node’lar ham xuddi Pod’lar kabi label ko’taradi. `nodeSelector` shuni aytadi:
faqat shu label’larga ega node’larni ko’rib chiq.

```bash
kubectl label nodes node01 size=large
kubectl get nodes --show-labels
kubectl get nodes -l size=large
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
spec:
  nodeSelector:
    size: large
  containers:
    - name: app
      image: data-processor:2.1
```

Scheduler `size=large` bo’lmagan har bir node’ni filtrlab tashlaydi va
qolganlariga odatdagidek ball beradi. Bironta node mos kelmasa, Pod aniq event
bilan Pending holatda qoladi:
`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`.

## Sizda allaqachon bor label’lar

Har bir node’da bilishga arziydigan o’rnatilgan label’lar to’plami bor, chunki
topshiriqlar ularni ishlatadi:

```bash
kubectl describe node node01 | grep -A12 Labels
```

| Label | Misol |
|---|---|
| `kubernetes.io/hostname` | `node01` |
| `kubernetes.io/os` / `kubernetes.io/arch` | `linux` / `amd64` |
| `node-role.kubernetes.io/control-plane` | control plane node’larida mavjud (qiymati bo’sh) |
| `topology.kubernetes.io/zone` / `region` | cloud provayderlar tomonidan qo’yiladi |
| `node.kubernetes.io/instance-type` | cloud instance hajmi |

```yaml
nodeSelector:
  kubernetes.io/hostname: node01     # bitta node'ga biriktirish, deklarativ yo'l
```

## Bu qayerda yetarli bo’lmay qoladi

`nodeSelector` - faqat AND orqali ishlaydigan tenglik: sanab o’tilgan har bir
label aynan mos kelishi kerak. Siz bularni ayta olmaysiz:

- "large **yoki** medium",
- "small’dan **boshqa** hamma narsa",
- "large afzal, lekin har qanaqasi ham bo’laveradi".

Bular uchun sizga keyingi darsdagi **node affinity** kerak; unda operatorlar
(`In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`) va *preferred* rejimi
bor. Qoida bitta yoki ikkita aniq label bo’lganda `nodeSelector` baribir
to’g’ri vosita bo’lib qoladi - yozish qisqaroq va xato qilish imkonsiz.

:::exam-tip
"Pod’ni `disktype=ssd` label’i qo’yilgan node’ga joylashtiring" degan
topshiriq - `nodeSelector` topshirig’i, affinity blokiga qo’l urmang.
"`size=large` **yoki** `size=medium` label’li node’ga" degan topshiriq esa -
affinity.
:::

## Node’larga label qo’yish, to’g’ri usulda

```bash
kubectl label nodes node01 disktype=ssd                 # qo'shish
kubectl label nodes node01 disktype=nvme --overwrite    # o'zgartirish
kubectl label nodes node01 disktype-                    # olib tashlash
kubectl label nodes -l kubernetes.io/os=linux tier=app  # bir vaqtda ko'pchilikka
```

:::warning
Node’lardagi label’lar boshqa hech qayerda saqlanmaydi: node qayta qurilsa,
provisioning uni qayta qo’ymasa, label yo’qoladi. kubeadm klasterida label
qayta qurishdan omon qoladigan joy - kubelet’ning `--node-labels` flag’i
(`/var/lib/kubelet/kubeadm-flags.env` ichida).
:::

## O’zingizni tekshiring

1. node01 ga `disktype=ssd` label’ini qo’yadigan va keyin o’sha label’ni olib
   tashlaydigan ikkita buyruqni yozing.
2. `nodeSelector` li Pod Pending holatda qoladi. Uning eventi nima deydi va
   siz qaysi ikki narsani tekshirasiz?
3. `nodeSelector` ifodalay olmaydigan, node affinity esa ifodalay oladigan
   ikkita talabni ayting.
