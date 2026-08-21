## Pod’larni node’lardan qaytarish

**Taint** - node’dagi belgi, u "ruxsatingiz bo’lmasa, bu yerga joylashmang"
deydi. **Toleration** - Pod’dagi mos belgi, u "menga ruxsat bor" deydi.
Taint’lar itaradi; toleration’lar ruxsat beradi. Ikkalasi ham *tortmaydi* -
toleration’li Pod taint qo’yilgan node’ga tushishi mumkin, lekin hech narsa
uni o’sha node’ni afzal ko’rishga majburlamaydi. Bu vazifa affinity’ga
tegishli.

```bash
kubectl taint nodes node01 spray=mortein:NoSchedule
kubectl describe node node01 | grep Taints
# Taints:  spray=mortein:NoSchedule
kubectl taint nodes node01 spray=mortein:NoSchedule-      # oxiridagi minus uni olib tashlaydi
```

Taint - bu `key=value:effect`. Effect - unga chidamaydigan Pod’larga nima
bo’lishi:

| Effect | Mavjud Pod’lar | Yangi Pod’lar |
|---|---|---|
| `NoSchedule` | qoladi | bu yerga joylashtirilmaydi |
| `PreferNoSchedule` | qoladi | boshqa node bo’lsa, chetlab o’tiladi |
| `NoExecute` | **chiqarib yuboriladi** (`tolerationSeconds` berilgan bo’lsa, o’shandan keyin) | bu yerga joylashtirilmaydi |

## Toleration yozish

```yaml
spec:
  tolerations:
    - key: spray
      operator: Equal
      value: mortein
      effect: NoSchedule
```

YAML nuqtai nazaridan har bir qator - qo’shtirnoqli satr (`value: "mortein"`),
operator esa `Equal` (kalit ham, qiymat ham mos kelishi kerak) yoki `Exists`
(faqat kalit; `value` ni yozmang). **Kalitsiz va `operator: Exists`** bo’lgan
toleration hamma narsaga chidaydi - ba’zi DaemonSet’lar har qanday node’da
shu tarzda ishlaydi.

```yaml
tolerations:
  - operator: Exists          # hamma taint'ga chidash
```

```yaml
tolerations:
  - key: node.kubernetes.io/not-ready
    operator: Exists
    effect: NoExecute
    tolerationSeconds: 300    # NotReady node'da 5 daqiqa turadi, keyin ketadi
```

Oxirgisi sukut bo’yicha har bir Pod’da bor - shuning uchun node bir necha
daqiqa "o’chib-yonganda" Pod’lar omon qoladi, node uzoq o’chiq qolsa esa
chiqarib yuboriladi.

## Control plane taint’i

```bash
kubectl describe node controlplane | grep Taints
# Taints:  node-role.kubernetes.io/control-plane:NoSchedule
```

kubeadm control plane node’larga taint qo’yadi, shunda oddiy workload’lar
ularga tushmaydi. Ikkita natijasi bor:

- Bitta node’li klasterda siz uni olib tashlamaguningizcha hech narsa
  joylashtirilmaydi
  (`kubectl taint nodes controlplane node-role.kubernetes.io/control-plane:NoSchedule-`).
- Control plane komponentlari va kube-proxy/CNI DaemonSet’larida unga
  toleration bor; ular o’sha yerda shuning uchun ishlaydi.

:::exam-tip
`0/2 nodes are available: 1 node(s) had untolerated taint {...}, 1 node(s)
...` eventi bilan Pending qotib qolgan Pod sizga butun voqeani aytib turibdi.
U nomlagan taint’ni o’qing va qaror qiling: uni Pod’da toleratsiya qilasizmi
(topshiriqda Pod o’sha yerda ishlashi kerak deyilgan) yoki node’dan olib
tashlaysizmi (topshiriqda node workload’larni qabul qilishi kerak deyilgan).
:::

## Taint’lar, toleration’lar va siz xohlagan narsa

Taint’lar node’ga qaratilgan: "bu node maxsus, keraksizlarni uzoqda tuting" -
GPU node’lari, jamoa uchun ajratilgan node’lar, texnik xizmatdagi node. Ular
"GPU Pod’larini *bu yerga* qo’y" demaydi. To’g’ri toleration’li GPU Pod’i
baribir oddiy node’ga joylashtirilishi mumkin. Ikkala yarmini - ajratilgan
node’lar **va** faqat o’sha yerga tushadigan Pod’larni - olish uchun taint’ni
**nodeSelector** yoki **node affinity** bilan birlashtirasiz; bu keyingi uchta
darsning mavzusi.

## Tezkor ma’lumotnoma

```bash
kubectl taint nodes node01 key=value:NoSchedule        # qo'shish
kubectl taint nodes node01 key=value:NoSchedule-       # olib tashlash
kubectl taint nodes node01 key:NoExecute-              # kalit+effect bo'yicha olib tashlash
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
kubectl run bee --image=nginx $do > bee.yaml           # keyin spec ostiga tolerations qo'shing
```

:::tip
`kubectl run --toleration` degan flag yo’q. YAML’ni generatsiya qiling,
blokni `spec:` ostiga (konteyner ostiga emas) qo’shing va apply qiling.
:::

## O’zingizni tekshiring

1. Node’da allaqachon ishlayotgan Pod uchun `NoSchedule` va `NoExecute`
   ta’siri orasidagi farq nima?
2. *Har qanday* taint’ga chidaydigan toleration yozing.
3. Node’da `env=prod:NoSchedule` taint’i bor va Pod unga chidaydi. Pod
   albatta o’sha node’da ishlaydimi? Buni kafolatlash uchun yana nima
   qo’shgan bo’lardingiz?
