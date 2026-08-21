## etcd nima

etcd - bu **taqsimlangan, izchil key-value store**. Sifatlarni olib tashlasangiz,
u oddiy lug’at: kalit ostiga qiymat qo’yasiz, kalit orqali uni qaytarib olasiz.
Sifatlarni qaytarsangiz, Kubernetes nega aynan uni tanlaganini ko’rasiz:

- **Taqsimlangan** - u a’zolar klasteri sifatida ishlaydi va ularning ozchiligi
  o’lsa ham ishlashda davom etadi.
- **Izchil** - har bir a’zo har bir qiymatga, tartibi bilan, rozi bo’ladi.
  O’qish hech qachon orqada qolgan a’zodan eskirgan javob qaytarmaydi. Aynan shu
  xususiyat klaster haqidagi *haqiqat*ni unda saqlashni xavfsiz qiladi.

Kubernetes hamma narsani etcd’da saqlaydi - har bir Pod, Service, Secret, Node,
ConfigMap, har bir RBAC qoidasi. API server, mohiyatan, etcd oldidagi
tekshiruvchi eshik. Agar etcd yo’qolsa, klasterda xotira qolmaydi; agar u sekin
bo’lsa, hamma narsa sekin.

## Kalitlar, qiymatlar va daraxt

etcd kalitlari tekis satrlar, lekin kelishuvga ko’ra ular yo’lga o’xshaydi va
Kubernetes bu kelishuvdan keng foydalanadi:

```
/registry/pods/default/web
/registry/deployments/kube-system/coredns
/registry/secrets/payroll/db-creds
```

Qiymatlar - serializatsiya qilingan obyektlar (JSON emas, protobuf, shuning
uchun ularni shunchaki ko’zingiz bilan o’qiy olmaysiz).

## etcdctl asoslari

`etcdctl` - bu klient. Har safar sozlanadigan uchta narsa:

```bash
export ETCDCTL_API=3          # v3 API - Kubernetes ishlatadigan yagona API
# va endpoint hamda TLS klient sertifikatlari, keyingi darsda ko'rib chiqiladi
```

Sizga kerak bo’ladigan fe’llar:

```bash
etcdctl put name "ahmad"           # yozish
etcdctl get name                   # o'qish -> kalit va qiymatni chiqaradi
etcdctl get name --print-value-only
etcdctl get / --prefix --keys-only # / ostidagi hamma kalitni ro'yxatlaydi
etcdctl del name                   # o'chirish

etcdctl endpoint health            # bu a'zo sog'lommi?
etcdctl endpoint status --write-out=table   # versiya, DB hajmi, leader, raft index
etcdctl member list                # klasterda kim bor
```

```bash
# Kubernetesga xos odat: bir turdagi obyektlarni to'g'ridan-to'g'ri etcd'dan sanash
etcdctl get /registry/pods --prefix --keys-only | wc -l
```

:::tip
`endpoint status` va `member list` ustidagi `--write-out=table` o’qib bo’lmaydigan
satrni leader belgilangan jadvalga aylantiradi. Har safar ishlating.
:::

## U qanday izchil qoladi: bir abzatsda RAFT

A’zolar **leader** saylaydi. Har bir yozuv leaderga boradi, u yozuvni o’z logiga
qo’shadi va follower’larga yuboradi; **ko’pchilik** (kvorum) uni yozgandan keyin
yozuv commit qilinadi va tasdiqlanadi. Agar leader o’lsa, follower’lar eng to’liq
logga ega bo’lganlar orasidan yangisini saylaydi. Yozuv uchun ko’pchilik kerak
bo’lgani sababli, N a’zoli klaster `(N-1)/2` a’zo yo’qotishiga chidaydi:

| A’zolar | Kvorum | Yo’qota oladi |
|---|---|---|
| 1 | 1 | 0 |
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 4 | 3 | 1 - 3 tadan yaxshi emas, shuning uchun hech qachon bunday qilmang |

Faqat toq sonlar. Ko’pchilik klasterlar uchun uchta, imkoningiz bo’lsa beshta.

:::exam-tip
Imtihon sizdan RAFT’ni sozlashni so’ramaydi. U sizdan **etcd’ni backup qilish va
tiklashni** (klaster xizmat ko’rsatish bosqichidagi topshiriq) hamda API server
ishlamayotganiga etcd sabab bo’lganini tanib olishni so’raydi. Kvorumni tushunish
"uchta etcd a’zosidan ikkitasi o’chgan - klasterga yozib bo’ladimi?" degan savol
ustida fikr yuritish imkonini beradi. (Yo’q.)
:::

## Boshlovchilar xato qiladigan ikki narsa

1. **"Bu ma’lumotlar bazasi-ku, so’rov yuboraman."** Kubernetes klasterida etcd’ga
   qo’lda yozmaysiz. Har bir yozuv API server orqali o’tadi, u tekshiradi, qabul
   qiladi va versiyalaydi. Kubernetes kalitiga `etcdctl put` qilish - klasterni
   buzish yo’li.
2. **"Backup - API serverning ishi."** Yo’q, sizning ishingiz. etcd o’zini backup
   qilmaydi; buni `etcdctl snapshot save` qiladi va uni rejalashtirish kerak.

## O’zingizni tekshiring

1. Nega Kubernetesga etcd faqat mavjud emas, balki *izchil* bo’lishi kerak?
2. Sizda beshta etcd a’zosi bor; ikkitasi o’chgan. Klaster yozuvlarni qabul qila
   oladimi? Nega?
3. Kubeadm klasteridagi deyarli har bir `etcdctl` buyrug’i qaysi environment
   variable va qaysi uchta flagni talab qiladi? (Buni keyingi darsda
   tasdiqlaysiz.)
