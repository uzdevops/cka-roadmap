## Ikki xil mashina

Kubernetes klasteri ikki rolga bo'lingan mashinalar ("node'lar") to'plamidir.

- **Control plane node'lari** qaror qabul qiluvchi komponentlarni ishga
  tushiradi: nima bo'lishi kerak, u qayerda ishlashi kerak va haqiqat unga mos
  keladimi.
- **Worker node'lar** haqiqiy konteynerlaringizni, shuningdek nima ishga
  tushirish kerakligini eshitish va tarmoqni ulash uchun zarur agentlarni
  ishga tushiradi.

Node ikkalasi ham bo'lishi mumkin. Bitta node'li `kind` yoki `minikube`
klasterida u aynan shunday.

```text
+---------------------------- Control plane ----------------------------+
|                                                                       |
|  kube-apiserver  <---->  etcd                                         |
|        ^                                                              |
|        |  kuzatish / yangilash                                        |
|        +-------- kube-scheduler                                       |
|        +-------- kube-controller-manager                              |
|        +-------- cloud-controller-manager (ixtiyoriy)                 |
+-----------------------------------------------------------------------+
             ^                                   ^
             | (kubelet xabar beradi, ish oladi) |
+------------+-----------+           +-----------+------------+
|      Worker node 1     |           |      Worker node 2     |
|  kubelet               |           |  kubelet               |
|  kube-proxy            |           |  kube-proxy            |
|  konteyner runtime     |           |  konteyner runtime     |
|  [ Pod ] [ Pod ]       |           |  [ Pod ]               |
+------------------------+           +------------------------+
```

## API server - yagona eshik

Kubernetesda etcd bilan API serverdan boshqa hech narsa gaplashmaydi. Ishni
rejalashtirish uchun kubelet bilan API serversiz hech narsa gaplashmaydi. Har
bir komponent - `kubectl`, scheduler, kontrollerlar, kubelet - bir xil REST
API'ning klienti.

Shu bitta fakt tizim xatti-harakatining ko'p qismini tushuntiradi:

- Kirish nazorati bitta joyda amalga oshiriladi (autentifikatsiya,
  avtorizatsiya, admission).
- Komponentlar bir-biridan mustaqil: scheduler kubelet borligini bilmaydi.
- Hamma narsa audit qilinadi, chunki har bir o'zgarish - API so'rovi.
- Agar API server ishlamasa, yangi hech narsa *rejalashtirilmaydi*, lekin
  ishlayotgan Pod'lar ishlashda davom etadi.

:::exam-tip
"API server ishlamayapti, lekin ilovam hali ham trafikka xizmat qilyapti" -
bu ziddiyat emas, va imtihon bu farqni yoqtiradi. Data plane (kubelet,
kube-proxy, konteynerlaringiz) ishlashda davom etadi; control plane shunchaki
yangi qaror qabul qila olmaydi yoki o'zgarishlarni qabul qila olmaydi.
:::

## Worker node'da nima ishlaydi

### kubelet

Har bir node'dagi agent. U API serverni *o'z* node'iga tayinlangan Pod'lar
uchun kuzatadi, so'ng konteyner runtime'ga ularni ishga tushirishni aytadi. U
node va Pod holatini qaytarib xabar qiladi. Shuningdek, lokal manifest
katalogidan **static Pod**larni ishga tushiradi - control plane odatda shu
tarzda ko'tariladi.

```bash
# kubeadm node'da:
sudo systemctl status kubelet
sudo journalctl -u kubelet -f          # NotReady node'da birinchi qaraladigan joy
ls /etc/kubernetes/manifests/          # static Pod manifestlari
```

### Konteyner runtime

Konteynerlarni haqiqatan ishga tushiradigan narsa; u bilan Container Runtime
Interface (CRI) orqali gaplashiladi. Bugun bu odatda **containerd** yoki
**CRI-O**. Docker Engine to'g'ridan-to'g'ri qo'llab-quvvatlanadigan runtime
sifatida Kubernetes 1.24 da olib tashlandi.

```bash
# containerd CLI'si, Kubernetes namespace'iga cheklangan
sudo crictl ps
sudo crictl images
sudo crictl logs <container-id>
```

### kube-proxy

Service'ning virtual IP'si haqiqiy Pod'ga yetib borishini ta'minlaydigan tarmoq
qoidalarini saqlaydi. `iptables` rejimida iptables zanjirlarini, `ipvs`
rejimida IPVS virtual serverlarini dasturlaydi. Ba'zi CNI plaginlari uni
butunlay eBPF bilan almashtiradi.

## `kubectl apply` ning yo'li

Buni boshdan-oxir kuzating - buni yodlashga arziydi, chunki nosozlik
aniqlashning yarmi qaysi bosqichni tekshirish kerakligini bilishdir.

1. **kubectl** kubeconfig'ni o'qiydi, HTTP so'rov quradi va uni API serverga
   yuboradi.
2. **Autentifikatsiya** - siz kimsiz? (klient sertifikati, bearer token, OIDC)
3. **Avtorizatsiya** - buni qilishga ruxsatingiz bormi? (RBAC)
4. **Admission control** - bu o'zgartirilishi yoki rad etilishi kerakmi?
   (avval mutating, keyin validating webhook'lar va o'rnatilgan plaginlar)
5. **Validatsiya va saqlash** - obyekt **etcd**ga yoziladi.
6. **Scheduler** `spec.nodeName` yo'q Pod'ni sezadi, node'larni filtrlaydi va
   baholaydi, so'ng binding yozadi.
7. **kubelet** tanlangan node'da o'ziga tayinlangan Pod'ni ko'radi va CRI
   runtime'ni chaqirib image tortadi hamda konteynerlarni ishga tushiradi.
8. **kube-proxy** va CNI plagini tarmoqni ulaydi, shunda Pod'ga murojaat
   qilish mumkin bo'ladi.
9. Holat kubelet orqali API serverga qaytadi va `kubectl get pods` `Running`
   ko'rsatadi.

```bash
# 5-9 bosqichlarni jonli kuzating
kubectl create deployment web --image=nginx:1.27
kubectl get events --sort-by=.lastTimestamp -w
```

:::tip
`kubectl get events --sort-by=.lastTimestamp` - butun imtihondagi eng qimmatli
yagona buyruq. Rejalashtirish, image tortish, probe va volume mount
nosozliklari - hammasi avval shu yerda o'zini bildiradi.
:::

## Yadro kabi tuyuladigan qo'shimchalar

Bular control plane ikkilik fayllar to'plamining qismi emas, lekin ularsiz
klaster ishlatib bo'lmaydigan holda qoladi:

- **CNI plagini** (Calico, Cilium, Flannel, ...) - har bir Pod'ga IP beradi va
  pod'lararo trafikni ishlatadi. Usiz node'lar `NotReady` bo'lib qoladi.
- **CoreDNS** - Service va Pod DNS nomlarini yechadi. `kube-system` ichida
  Deployment sifatida ishlaydi.
- **metrics-server** - `kubectl top` va Horizontal Pod Autoscaler'ni
  ta'minlaydi.

```bash
kubectl get pods -n kube-system
kubectl get nodes -o wide
```

:::warning
Yangi `kubeadm init` CNI plagini o'rnatilmaguncha har bir node'ni `NotReady`
holatida qoldiradi. Bu kutilgan xatti-harakat, buzilgan klaster emas - kubelet
tarmoq plagini sozlanmagani uchun `NetworkReady=false` deb xabar beradi. Qayta
o'rnatishga kirishishdan oldin node holatlarini o'qing:

```bash
kubectl describe node <node> | grep -A10 Conditions
```
:::

## O'zingizni tekshiring

1. Pod qaysi node'da ishlashini qaysi komponent hal qiladi va uni aslida qaysi
   komponent ishga tushiradi?
2. Agar etcd mavjud bo'lmasa, nima ishlashda davom etadi va nima to'xtaydi?
3. Nega node `Ready` bo'lishi mumkin, lekin undagi Pod boshqa Pod'dan hali ham
   murojaat qilib bo'lmaydigan bo'lishi mumkin?
