## Mukammal bilishingiz shart bo’lgan to’rtta komponent

`kubeadm` klasterida bularning barchasi control plane node’da **static Pod**
sifatida ishlaydi va `/etc/kubernetes/manifests/` ichidagi manifestlar orqali
aniqlanadi. Kubelet o’sha katalogni kuzatadi va ularni ishlab turgan holda
ushlab turadi - bu chiroyli bootstrap hiylasi: control plane’ni u boshqaradigan
agentning o’zi ishga tushiradi.

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml

kubectl get pods -n kube-system -l tier=control-plane
```

## kube-apiserver

Kirish eshigi. Stateless, gorizontal masshtablanadi va etcd bilan gaplashadigan
yagona komponent.

Uning so’rov konveyerini nomma-nom bilish arziydi, chunki imtihondagi
nosozliklar aynan shunga tushadi:

```text
request -> authentication -> authorisation (RBAC) -> admission -> validation -> etcd
             401                403                  4xx/mutation
```

Amalda tegadigan asosiy flaglar:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml (qismi)
spec:
  containers:
    - command:
        - kube-apiserver
        - --advertise-address=10.0.0.10
        - --secure-port=6443
        - --etcd-servers=https://127.0.0.1:2379
        - --authorization-mode=Node,RBAC
        - --enable-admission-plugins=NodeRestriction
        - --client-ca-file=/etc/kubernetes/pki/ca.crt
```

:::warning
Bu faylni tahrirlash API server’ni bir necha soniya ichida qayta ishga
tushiradi. Bitta xato yozuv API server umuman qaytmasligini va `kubectl`
butunlay ishlamay qolishini bildiradi. Har doim nusxasini saqlang:

```bash
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/apiserver.yaml.bak
```

Agar buzib qo’ysangiz, `kubectl` o’lgan bo’lsa ham konteyner loglari diskda
qolaveradi:

```bash
sudo crictl ps -a | grep apiserver
sudo crictl logs <container-id>
```
:::

## etcd

Taqsimlangan, izchil kalit-qiymat ombori. U klasterning **barcha** holatini
saqlaydi - siz yaratgan har bir obyektni. Bu yagona stateful komponent, shuning
uchun haqiqatan backup qilishingiz shart bo’lgan yagona narsa ham shu.

- Raft konsensus algoritmidan foydalanadi; `(n/2)+1` a’zodan iborat kvorum
  talab qiladi.
- Shuning uchun har doim **toq** sonli a’zo ishlating: 3 yoki 5. 2 a’zoli
  klaster 1 a’zoli klasterdan qat’iy yomonroq.
- Watch’lar butun moslashtirish modelini samarali qiladi - kontrollerlar
  so’rab turish o’rniga o’zgarishlarga obuna bo’ladi.

```bash
# Klaster salomatligi, control plane'ning o'z sertifikatlari bilan
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

:::exam-tip
etcd backup va tiklash CKA’da katta ehtimol bilan uchraydi. Buyruq shakli har
doim bir xil - endpoints, cacert, cert, key - va bu yo’llarning har birini
to’g’ridan-to’g’ri `/etc/kubernetes/manifests/etcd.yaml` faylidan o’qib olasiz.
To’liq snapshot save/restore tsiklini 4-bosqichda mashq qilasiz.
:::

## kube-scheduler

`spec.nodeName` si yo’q Pod’larni kuzatadi va node’ni ikki bosqichda tanlaydi:

1. **Filtrlash** ("predicates") - ishlay *olmaydigan* node’larni chiqarib
   tashlaydi: yetarli allocatable CPU/xotira yo’q, Pod chidamaydigan taint’lar,
   bajarilmagan node selector yoki affinity, mos volume topologiyasi yo’q, node
   `Ready` emas.
2. **Ball berish** ("priorities") - omon qolganlarni saralaydi: node’lar
   bo’ylab tarqatish, image lokalligi, eng kam so’ralgan resurslar, affinity
   afzalliklari.

Eng yuqori ball to’plagan node yutadi va scheduler **Binding** obyektini
yozadi. U hech qachon kubelet bilan bog’lanmaydi.

```bash
# Bu Pod nega Pending? Scheduler buni event'larda aytadi.
kubectl describe pod <name> | tail -20
# Events:
#   Warning  FailedScheduling  0/3 nodes are available:
#   1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
#   2 Insufficient cpu.
```

Bu xabar - filtrlash bosqichining tushuntirishi. Uni so’zma-so’z o’qing: u
qaysi predikat qaysi node’larni rad etganini aniq aytib beradi.

## kube-controller-manager

O’nlab mustaqil boshqaruv tsiklini ishga tushiradigan yagona binar. Eng ko’p
uchraydiganlari:

| Kontroller | Mas’uliyati |
| --- | --- |
| Deployment | Rollout’lar uchun ReplicaSet yaratadi va masshtablaydi |
| ReplicaSet | Pod’larning to’g’ri sonini tirik saqlaydi |
| Node | Node’larni nosog’lom deb belgilaydi va grace period’dan keyin Pod’larni evict qiladi |
| Job / CronJob | Pod’larni jadval bo’yicha oxirigacha bajaradi |
| Endpoints / EndpointSlice | Service backend’larini Pod readiness’i bilan sinxron ushlab turadi |
| ServiceAccount + Token | Yangi namespace’larda default ServiceAccount yaratadi |
| PersistentVolume | Claim’larni volume’larga bog’laydi, reclaim policy’ni boshqaradi |

```bash
kubectl get deployment web -o yaml | grep -A5 'status:'
# observedGeneration kontroller oxirgi o'zgarishingizni ko'rgan-ko'rmaganini aytadi
```

## cloud-controller-manager

Ixtiyoriy va bare-metal yoki lokal klasterlarda yo’q. U bulutga xos mantiqni
ajratib turadi: `type: LoadBalancer` Service’lar uchun load balancer yaratish,
bulut disklarini ulash va node’larni region/zone bilan belgilash.

:::tip
`kind` yoki `minikube`’da cloud controller yo’q, shuning uchun
`type: LoadBalancer` Service tashqi IP’si uchun abadiy `<pending>` bo’lib
qolaveradi. Bu to’g’ri xatti-harakat, xato emas. Lokalda `NodePort`,
`kubectl port-forward` yoki `minikube tunnel`’dan foydalaning.
:::

## Nosozlik holatlari, komponent bo’yicha

Bu jadval - darsdagi eng tez takrorlash vositasi.

| Ishlamay qolgan komponent | Alomat |
| --- | --- |
| kube-apiserver | `kubectl` butunlay ishlamaydi; ishlayotgan Pod’larga ta’sir qilmaydi |
| etcd | API server nosog’lom; klaster holatini o’qish ham, yozish ham yo’q |
| kube-scheduler | Yangi Pod’lar abadiy `Pending` qoladi; mavjudlari joyida |
| kube-controller-manager | O’chirilgan Pod’lar qayta yaratilmaydi; rollout’lar to’xtaydi; node’lar hech qachon NotReady deb belgilanmaydi |
| kubelet (bitta node) | O’sha node `NotReady` bo’ladi; undagi Pod’lar oxir-oqibat evict qilinadi |
| kube-proxy (bitta node) | Service VIP’lari o’sha node *dan* ishlamay qoladi |
| CoreDNS | DNS hal qilish ishlamaydi; ilovalar hostname qidiruvida xato beradi |

:::exam-tip
Alomat berilganda komponentni ayting. "Yangi Pod’lar Pending, lekin mavjudlari
sog’lom" - bu scheduler. "Deployment’dan Pod o’chirdim va u hech qachon
almashtirilmadi" - bu controller manager. Bu moslikni ikki tomonga ham mashq
qiling - nosozlikni bartaraf etish imtihonning 30% ini tashkil qiladi.
:::

## O’zingizni tekshiring

1. kubeadm node’da control plane manifestlari qayerda turadi va ulardan birini
   tahrirlaganingizda ularni nima qayta ishga tushiradi?
2. Nega etcd klasterida a’zolar soni toq bo’lishi shart?
3. Pod `Pending` holatida va `FailedScheduling: Insufficient cpu` deyapti.
   Rejalashtirishning qaysi bosqichi uni rad etdi va buni tuzatishning ikki
   yo’li qanday?
