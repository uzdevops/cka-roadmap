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

## Klasterga umumiy nazar

Quyidagilarning hammasi - diagrammadagi qutilar, ikkita sarlavha ham shunga
kiradi. Istalganini bosing va uning tavsifiga tushasiz: u nima qiladi,
to'xtaganda nima buziladi va amalda qaysi buyruqni yozasiz.

::cluster-architecture

:::component{key=control-plane}
Bu jarayon emas - node bajaradigan **rol**. Control plane node'i quyidagi
to'rtta komponentni ishlatadi va ular birgalikda bitta savolga qayta-qayta
javob beradi: klaster so'ralgan holatga mos keladimi? Ularning hech biri sizning
ilova konteynerlaringizni ishlatmaydi.

Ishlab chiqarish klasterlarida load balancer ortida uchta yoki beshta control
plane node'i turadi - shunda bittasi ishdan chiqqanda ham API server
mavjudligicha qoladi va etcd kvorumini saqlaydi. `kind` yoki `minikube` esa
bularning hammasini bitta node'ga yig'adi: u ham control plane, ham worker.

`kubeadm` klasterida to'rttalasi ham **static Pod** sifatida ishlaydi; ularning
manifestlarini kubelet kuzatib turadi:

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml

kubectl get pods -n kube-system -l tier=control-plane
```

Control plane node'lari odatda oddiy workload'larni o'ziga qo'ymaydigan taint
bilan keladi - yarmi bo'sh ko'rinadigan ikki node'li klasterda Pod nega
`Pending` bo'lib turishining sababi ham shu:

```bash
kubectl describe node <control-plane-node> | grep -i taint
# Taints: node-role.kubernetes.io/control-plane:NoSchedule
```
:::

:::component{key=kube-apiserver}
Old eshik va etcd bilan gaplashadigan yagona komponent. Qolgan hamma narsa -
`kubectl`, scheduler, kontrollerlar, har bir kubelet - shu bitta REST API'ning
klienti. Aynan shuning uchun kirish nazorati, audit va validatsiya bitta joyda
sodir bo'ladi.

U stateless va gorizontal kengayadi: u xizmat qiladigan barcha holat etcd'da
yotadi. So'rov quvuri bosqichlarini nomi bilan bilish kerak, chunki nosozliklar
aynan shu bosqichlarga tushadi:

```text
so'rov -> autentifikatsiya -> avtorizatsiya (RBAC) -> admission -> validatsiya -> etcd
              401                  403                 4xx/mutation
```

**Ishlamay qolsa:** `kubectl` butunlay to'xtaydi va yangi qaror qabul qilinmaydi
- lekin allaqachon ishlayotgan Pod'lar ishlashda va trafikka xizmat qilishda
davom etadi. Data plane unga bog'liq emas.

```bash
kubectl get --raw='/readyz?verbose'
sudo crictl ps -a | grep apiserver     # kubectl ishlamaganda ham ishlaydi
```
:::

:::component{key=etcd}
Taqsimlangan, izchil kalit-qiymat ombori; u klasterning **butun** holatini -
siz yaratgan har bir obyektni saqlaydi. Bu control plane'dagi yagona stateful
komponent, shuning uchun zaxira nusxa olish kerak bo'lgan yagona narsa ham shu.

- Raft konsensus algoritmidan foydalanadi va `(n/2)+1` kvorumni talab qiladi.
- Shuning uchun har doim **toq** sonda a'zo ishlating: 3 yoki 5. 2 a'zoli
  klaster 1 a'zolidan qat'iy yomonroq: u bitta ham nosozlikka bardosh
  bermaydi, buziladigan narsa esa ikkita.
- Uning **watch** mexanizmi reconciliation'ni samarali qiladi - kontrollerlar
  so'rov yuborib turmaydi, o'zgarishlarga obuna bo'ladi.

**Ishlamay qolsa:** API server o'zini nosog'lom deb e'lon qiladi va klaster
holatini na o'qib, na yozib bo'ladi.

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```
:::

:::component{key=kube-controller-manager}
O'nlab mustaqil boshqaruv siklini ishlatuvchi bitta ikkilik fayl. Har bir sikl
API server orqali kerakli holatni kuzatadi, uni kuzatilgan holat bilan
solishtiradi va farqni yopish uchun harakat qiladi. Reconciliation modeli
amalda shu.

| Kontroller | Vazifasi |
| --- | --- |
| Deployment | Rollout uchun ReplicaSet yaratadi va masshtablaydi |
| ReplicaSet | Kerakli sondagi Pod'ni tirik saqlaydi |
| Node | Nosog'lom node'larni belgilaydi va muhlatdan so'ng Pod'larni ko'chiradi |
| Job / CronJob | Pod'larni yakunigacha, jadval bo'yicha ishlatadi |
| EndpointSlice | Service backend'larini Pod tayyorligiga moslab turadi |
| PersistentVolume | Claim'larni volume'larga bog'laydi, reclaim siyosatini bajaradi |

**Ishlamay qolsa:** o'chirilgan Pod'lar qayta yaratilmaydi, rollout'lar yarim
yo'lda qotadi va ishdan chiqqan node'lar hech qachon `NotReady` deb
belgilanmaydi. Hech narsa baland ovozda xato bermaydi - klaster shunchaki
o'zini davolashni to'xtatadi.
:::

:::component{key=kube-scheduler}
Hali `spec.nodeName`i yo'q Pod'larni kuzatadi va ularning har biriga node
tanlaydi, ikki bosqichda:

1. **Filtrlash** ("predicates") - *ishlay olmaydigan* node'larni chiqarib
   tashlaydi: allocatable CPU yoki xotira yetmasligi, Pod tolerate qilmaydigan
   taint'lar, bajarilmagan node selector yoki affinity, mos volume topologiyasi
   yo'qligi, node `Ready` emasligi.
2. **Baholash** ("priorities") - omon qolganlarni tartiblaydi: node'lar bo'ylab
   taqsimlash, image lokalligi, eng kam so'ralgan resurslar, affinity
   afzalliklari.

Eng yuqori ball olgan node yutadi va scheduler **Binding** obyektini yozadi. U
hech qachon kubelet bilan bog'lanmaydi - faqat API serverga yozadi, kubelet esa
kuzatib turgani uchun bundan xabar topadi.

**Ishlamay qolsa:** yangi Pod'lar abadiy `Pending` bo'lib qoladi; allaqachon
ishlayotganlariga hech nima bo'lmaydi.

```bash
kubectl describe pod <name> | tail -20
# Events:
#   Warning  FailedScheduling  0/3 nodes are available:
#   1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
#   2 Insufficient cpu.
```

Bu xabar - filtrlash tushuntirishi. Uni so'zma-so'z o'qing: qaysi predicate
qaysi node'larni rad etganini aynan aytib beradi.
:::

:::component{key=worker}
Ikkinchi rol: konteynerlaringizni haqiqatan ishlatadigan node'lar. Worker
quyidagi uchta komponentni va Pod'larning o'zini saqlaydi hamda **hech qanday
qaror qabul qilmaydi** - unga nima ishlatish kerakligi aytiladi, u esa natijani
qaytarib xabar qiladi.

Klasterning **data plane** deb ataladigan yarmi aynan shu, va buzilgan control
plane bilan yashab bo'lishining sababi ham shu: worker'lar nima ishlatayotganini
allaqachon biladi va davom ettiraveradi. Trafik oqaveradi; siz shunchaki hech
narsani o'zgartira olmaysiz.

Xohlaganingizcha qo'shavering - klaster aynan worker'lar bo'yicha
masshtablanadi. Har biriga kubelet, konteyner runtime, kube-proxy (yoki uni
almashtiradigan CNI) va Pod'lariga manzil beradigan CNI plagini kerak.

```bash
kubectl get nodes -o wide
kubectl describe node <node> | grep -A10 Conditions   # node nega NotReady
kubectl get pods -A -o wide --field-selector spec.nodeName=<node>
```

:::exam-tip
`kubectl drain <node> --ignore-daemonsets`, so'ng `kubectl uncordon <node>` -
imtihon eng ko'p so'raydigan worker node hayotiy sikli. Drain Pod'larni
ko'chiradi va node'ni rejalashtirib bo'lmaydigan qilib belgilaydi;
`--ignore-daemonsets` kerak, chunki DaemonSet Pod'lari ataylab ko'chiriladigan
qilib qo'yilmagan.
:::
:::

:::component{key=kubelet}
**Har bir** node'dagi agent, control plane node'lari ham bunga kiradi. U API
serverni *o'z* node'iga tayinlangan Pod'lar uchun kuzatadi, so'ng konteyner
runtime'ga ularni ishga tushirishni aytadi va node hamda Pod holatini yuqoriga
qaytarib xabar qiladi.

Shuningdek, u lokal manifest katalogidan **static Pod**larni to'g'ridan-to'g'ri,
scheduler ishtirokisiz ishga tushiradi. Control plane o'zini shu tarzda
ko'taradi: `kubeadm` klasterida API server, etcd, scheduler va controller
manager - hammasi o'zi boshqaradigan kubelet ishlatadigan static Pod'lar.

**Bitta node'da ishlamay qolsa:** o'sha node `NotReady` bo'ladi va eviction
muhlatidan so'ng uning Pod'lari boshqa joyga ko'chiriladi. Unda allaqachon
ishlab turgan konteynerlarni kubelet yo'qligi o'ldirmaydi - shunchaki ular
haqida xabar beradigan yoki ularni qayta ishga tushiradigan hech kim qolmaydi.

```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -f          # NotReady node'da birinchi qaraladigan joy
ls /etc/kubernetes/manifests/          # static Pod manifestlari
```
:::

:::component{key=kube-proxy}
Service'ning virtual IP'si haqiqiy Pod'ga yetib borishini ta'minlaydigan tarmoq
qoidalarini saqlaydi. U Service va EndpointSlice'larni kuzatadi va node'ning
paket uzatish qatlamini ularga moslab dasturlaydi.

- `iptables` rejimida iptables zanjirlarini yozadi - odatiy standart shu.
- `ipvs` rejimida IPVS virtual serverlarini dasturlaydi; juda ko'p Service'li
  klasterlarda bu yaxshiroq masshtablanadi.
- Ba'zi CNI plaginlari (masalan, Cilium) uni butunlay eBPF bilan almashtiradi.

**Bitta node'da ishlamay qolsa:** Service VIP'lari *o'sha node'dan* ishlamay
qoladi. Undagi Pod'larga Pod IP orqali to'g'ridan-to'g'ri murojaat qilish esa
ishlayveradi - aynan shu ipuchi CNI plaginiga emas, kube-proxy'ga ishora
qiladi.

```bash
kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide
sudo iptables -t nat -L KUBE-SERVICES -n | head
```
:::

:::component{key=container-runtime}
Konteynerlarni haqiqatan ishga tushiradigan narsa: image tortadi, namespace va
cgroup yaratadi, jarayonlarni boshlaydi va to'xtatadi. Kubelet u bilan
**Container Runtime Interface (CRI)** orqali gaplashadi, shuning uchun ikkalasi
almashtiriladigan.

Bugun bu odatda **containerd** yoki **CRI-O**. Docker Engine to'g'ridan-to'g'ri
qo'llab-quvvatlanadigan runtime sifatida Kubernetes 1.24 da olib tashlandi; u
qurgan image'larga bu ta'sir qilmaydi, chunki image formati va runtime - alohida
narsalar.

**Bitta node'da ishlamay qolsa:** kubelet u yerda hech narsani ishga tushira
olmaydi va node `NotReady` bo'ladi - bu o'lgan kubelet bilan bir xil alomat,
shuning uchun ikkalasini ham tekshirasiz.

```bash
sudo crictl ps                 # containerd CLI'si, Kubernetes namespace'iga cheklangan
sudo crictl images
sudo crictl logs <container-id>
```
:::

:::note
Ba'zi klasterlarda sakkizinchi quti ham bor: **cloud-controller-manager**. U
ixtiyoriy va bare metal, `kind` hamda `minikube`da mavjud emas. U bulutga xos
mantiqni ajratadi: `type: LoadBalancer` Service'lari uchun load balancer
yaratish, bulut disklarini ulash, node'larni region va zona bilan belgilash.
Lokalda uning yo'qligi sababli `type: LoadBalancer` Service'ining tashqi IP'si
abadiy `<pending>` bo'lib qoladi - bu xato emas, to'g'ri xatti-harakat.
:::

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
