## Pod’ning manzilini kim hal qiladi

Har safar Pod ishga tushganda CNI plugin’dan IP so’raladi. U qayerdan keladi
va ikki node bir xil IP’ni tarqatib yubormasligi qanday ta’minlanadi? Bu -
**IP Address Management**, va CNI spetsifikatsiyasi uni alohida,
almashtirsa bo’ladigan qadam qilib qo’ygan: tarmoq plugin’i o’z config’ida
nomi ko’rsatilgan **IPAM plugin**’ni chaqiradi.

```json
"ipam": {
  "type": "host-local",
  "subnet": "10.244.1.0/24",
  "routes": [{"dst": "0.0.0.0/0"}]
}
```

## Ikkita reference IPAM plugin

| Plugin | Qayerdan ajratadi | Ajratmalarni qayerda qayd etadi |
|---|---|---|
| `host-local` | config’da berilgan subnet - Pod CIDR’ining **shu node’ga tegishli** bo’lagi | node’dagi fayllar: `/var/lib/cni/networks/<name>/<ip>` (har bir manzil uchun bitta fayl, ichida konteyner ID’si) |
| `dhcp` | tarmoqdagi DHCP server | DHCP serverning lease’lari (lease’larni tirik saqlash uchun node’da `dhcp` demoni ishlaydi) |

```bash
ls /var/lib/cni/networks/cbr0/
# 10.244.1.2  10.244.1.3  last_reserved_ip.0  lock
cat /var/lib/cni/networks/cbr0/10.244.1.2      # uni band qilib turgan konteyner ID'si
```

Flannel aynan `host-local` ga topshiradi va ko’p plugin’lar uni ichki
qismida ishlatadi. Node’lar orasidagi betakrorlik oddiy: har bir node’da
**boshqa subnet** bo’ladi, shuning uchun ikki node to’qnasha olmaydi - node
ichida esa fayllar daftar vazifasini bajaradi.

## Har bir node’ning subnet’i qayerdan keladi

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
# controlplane   10.244.0.0/24
# node01         10.244.1.0/24
# node02         10.244.2.0/24
```

**Controller manager** (`--allocate-node-cidrs=true`,
`--cluster-cidr=10.244.0.0/16`, `--node-cidr-mask-size=24`) klasterning Pod
CIDR’ini har bir node uchun `/24` larga bo’lib chiqadi va har birini
`node.spec.podCIDR` ga yozadi. CNI DaemonSet’i buni o’qiydi va node’ning
IPAM config’iga yozadi. Ya’ni zanjir shunday: `kubeadm init --pod-network-cidr`
→ controller manager flag’lari → `node.spec.podCIDR` → CNI config →
`host-local` → Pod IP.

Har bir node’ga bitta `/24` - bu **ko’pi bilan node’ga 254 ta Pod** -
kubelet’ning sukut bo’yicha `maxPods=110` sozlamasini hisobga olsak, yetib
ortadi, lekin aynan shu sabab `/16` klaster CIDR’i 256 ta node’da to’xtaydi.

## O’z IPAM’i bor plugin’lar

Calico va Cilium `host-local` ni ishlatmaydi. Calico’ning IPAM’i node’larga
IP pool’lardan talab bo’yicha kichikroq bloklar (`/26`) beradi, shuning
uchun ko’p Pod ishlatadigan node bir nechtasini olishi mumkin, kam
ishlatadigani esa `/24` ni behuda sarflamaydi; daftarni fayllarda emas,
Kubernetes API’sida saqlaydi (Calico’ning `IPAMBlock` CRD’lari). G’oya
o’sha-o’sha - daftar va betakrorlik kafolati - faqat moslashuvchanroq.

```bash
kubectl get ippools.crd.projectcalico.org -o yaml 2>/dev/null | grep cidr
calicoctl ipam show 2>/dev/null
```

:::exam-tip
Imtihon savoli odatda "node01’dagi Pod’larga qaysi diapazondan manzil
beriladi" (`node.spec.podCIDR`) yoki "bu CNI qaysi IPAM’ni ishlatadi"
(`/etc/cni/net.d` dagi faylning `ipam` blokini o’qing) shaklida bo’ladi.
Event’larida `failed to allocate
for range` bilan qotib qolgan Pod - o’sha node’ning subnet’i tugagani yoki
IPAM daftari tiqilib qolgani; qattiq qayta yuklashdan keyin
`/var/lib/cni/networks` da qolib ketgan eski fayllar - ma’lum sabab, va
o’sha eski yozuvlarni o’chirish buni tuzatadi.
:::

## O’zingizni tekshiring

1. Odatiy CNI config’ida Pod IP’sini aslida qaysi plugin tanlaydi va u
   nimani tarqatganini qayerda qayd etadi?
2. `node.spec.podCIDR` ni kim tayinlaydi va qaysi flag asosida?
3. Nega `host-local` ishlatadigan ikki node hech qachon bir xil IP ajrata
   olmaydi?
