## Ikkita plugin nuqtasi

Docker’ning storage’i ikkita narsaga bo’linadi va har birining o’z plugin
interfeysi bor:

| Nima haqda | Plugin turi | Sukut bo’yicha | Misollar |
|---|---|---|---|
| image qatlamlari fayl tizimiga qanday yig’ilishi | **storage driver** | `overlay2` | aufs, devicemapper, btrfs, zfs |
| **volume** aslida qayerda yashashi | **volume driver** | `local` (`/var/lib/docker/volumes`) | RexRay, Portworx, Convoy, NetApp, GlusterFS, vSphere plugin’lari |

Storage driver image’lar va konteyner qatlami haqida - dizayni bo’yicha
vaqtinchalik. Volume driver esa siz saqlab qolmoqchi bo’lgan ma’lumot haqida
va aynan u **hostdan tashqariga** chiqa oladi.

```bash
docker volume create --driver local my-vol
docker run -v my-vol:/data alpine

docker plugin install rexray/ebs EBS_ACCESSKEY=... EBS_SECRETKEY=...
docker run -it --volume-driver rexray/ebs --mount src=ebs-vol,target=/data mysql
```

RexRay EBS driver’i bilan volume - bu AWS EBS diski: konteynerni bir hostda
to’xtatib, boshqasida ishga tushirish mumkin va o’sha ma’lumot joyida bo’ladi.
Kubernetes’ga kerak bo’lgan imkoniyat ham shu - workload ortidan node’lar
bo’ylab yuradigan storage.

## Kubernetes nega Docker’ning volume driver’larini olmadi

Kubernetes Docker’ning volume plugin’lariga hech qachon bog’lanmagan; buning
uchta sababi bor va ular birgalikda keyingi darsni tushuntiradi:

1. Kubernetes bir nechta konteyner runtime’ida ishlaydi (containerd, CRI-O),
   shuning uchun volume tushunchasi runtime’dan mustaqil bo’lishi kerak edi.
2. Kubernetes’ning o’z dastlabki storage plugin’lari **in-tree** edi: AWS EBS,
   GCE PD, Azure Disk, NFS, Ceph va qolganlarining kodi Kubernetes’ning o’ziga
   kompilyatsiya qilingan edi. Har bir vendor o’zgarishi Kubernetes relizini
   talab qilardi; har bir vendor xatosi Kubernetes’ning xatosi edi.
3. Vendorlarga bir marta yozib, uni har qanday orkestrator bilan ishlata
   oladigan yagona interfeys kerak edi.

Javob **Container Storage Interface (CSI)** bo’ldi - runtime’lar uchun CRI va
tarmoq uchun CNI’ning storage’dagi ekvivalenti - va o’shandan beri in-tree
plugin’lar CSI driver’lariga ko’chirildi. Kubernetes 1.30+ deyarli hech qanday
in-tree bulut storage kodini olib yurmaydi.

```
Runtime  ─── CRI ──▶ containerd, CRI-O
Network  ─── CNI ──▶ Calico, Flannel, Cilium, Weave
Storage  ─── CSI ──▶ EBS CSI, GCE PD CSI, Ceph CSI, NFS CSI, Portworx, ...
```

:::tip
Bitta narsani eslab qolsangiz: Docker’ning volume driver’lari - g’oya edi;
CSI - o’sha g’oya aylangan standart, va Kubernetes’da siz faqat CSI tomonini
uchratasiz - `ebs.csi.aws.com` kabi `provisioner` ko’rsatuvchi
**StorageClass** sifatida.
:::

## Buni klasterda ko’rish

```bash
kubectl get csidrivers                 # bu klasterda ro'yxatdan o'tgan CSI driver'lar
kubectl get csinodes                   # har bir node'da qaysi driver'lar bor
kubectl get storageclass               # PROVISIONER ustuni driver nomini beradi
kubectl get pods -n kube-system | grep csi    # driver'ning controller va node Pod'lari (DaemonSet)
```

CSI driver’i yo’q klaster ham `hostPath`, `local` va NFS volume’laridan
foydalana oladi - lekin hech narsani dinamik ta’minlay olmaydi; StorageClass
darsi aynan shu haqda.

## O’zingizni tekshiring

1. Docker’da storage driver va volume driver orasidagi farq nima?
2. Kubernetes nega o’z storage plugin’larini tree’dan tashqariga chiqardi va
   ularni qaysi interfeys almashtirdi?
3. Klasterda qaysi storage driver’lar o’rnatilganini qayerdan ko’rasiz?
