## Bir necha mashina bo’ylab izchillik

Bitta etcd a’zosi - ma’lumotlar bazasi. Uchtasi esa **taqsimlangan**
ma’lumotlar bazasi bo’lib, ular biri o’chgan yoki sekin bo’lganda ham har bir
yozuvda, tartib bilan, kelishuvga kelishi shart. Ularni kelishtiruvchi
protokol - **RAFT**, va uning shaklini bilish "nechtasini yo’qota olaman"
degan har qanday savolni mulohaza qilib yechish imkonini beradi.

## Leader, follower’lar va bitta yozuv

Istalgan paytda a’zolardan biri **leader**, qolganlari **follower** bo’ladi.
Har bir yozuv leaderga boradi (follower’lar uni uzatib yuboradi). Leader:

1. yozuvni o’z logiga qo’shadi,
2. uni follower’larga yuboradi,
3. a’zolarning **ko’pchiligi** (o’zi ham hisobga olinadi) uni yozguncha
   kutadi,
4. uni commit qiladi, qo’llaydi va mijozga tasdiq beradi,
5. follower’larga commit qilishni aytadi.

O’qishlar ham sukut bo’yicha leader orqali o’tadi (linearizable), shunda o’qish
hech qachon oldin tasdiqlangan yozuv ko’rsatmaydigan narsani qaytarmaydi.
Kubernetes tayanadigan izchillik shu: agar API server’ga "Pod yaratildi"
deyilgan bo’lsa, keyingi har bir o’qish uni ko’radi.

## Kvorum

| A’zolar (N) | Kvorum (N/2 + 1) | Chidaladigan nosozliklar |
|---|---|---|
| 1 | 1 | 0 |
| 2 | 2 | 0 - 1 tadan ham yomonroq |
| 3 | 2 | 1 |
| 4 | 3 | 1 - 3 tadan yaxshiroq emas |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

Nega "ko’pchilik" va nega "hamma" emas: hammani kutish bitta sekin yoki o’lgan
a’zo butun dunyoni to’xtatishini anglatadi. Nega "ko’pchilik" va nega
"istalgan biri" emas: bo’lingan tarmoqning ikki yarmi ham yozuvlarni qabul
qilib, bir-biridan uzoqlashib ketishi mumkin edi. Ko’pchilik esa faqat bitta
tomonda bo’la oladi.

Toq sonlar, chunki juft son chidaladigan nosozliklar sonini oshirmasdan
kvorumni oshiradi. **Uchta - standart, kritik klasterlar uchun beshta,
yettitadan ko’pi hech qachon tavsiya etilmaydi** - har bir yozuv ko’proq
replikatsiyani kutadi.

## Leader saylovi

Follower’lar leaderdan heartbeat kutadi. Agar biri ularni eshitmay qolsa
(**saylov taymauti**, sukut bo’yicha ~1 s), u **nomzod**ga aylanadi, term
raqamini oshiradi va ovoz so’raydi; ovozlarning ko’pchiligi uni leader qiladi.
Teng va tengga yaqin holatlar tasodifiy taymautlar bilan hal qilinadi. Saylov
davomida - bir soniyacha - yozuvlar ishlamaydi va API server loglarga xato
yozadi; Kubernetes mijozlari qayta uradi. Kvorumsiz qolgan klaster (uchtadan
ikkitasi o’chgan) **leader saylay olmaydi va yozuvlarga xizmat qila olmaydi**;
u yaxshi holatda eskirgan o’qishlarni beradi. Tanib olish kerak bo’lgan holat
shu: `kubectl get` ba’zan ishlaydi, `kubectl create` osilib qoladi, etcd
loglari esa "no leader" bilan to’la.

```bash
etcdctl endpoint status --cluster --write-out=table     # IS LEADER ustuni, raft term va index
etcdctl endpoint health --cluster
etcdctl member list --write-out=table
```

## Topologiya

**Stacked** (kubeadm’ning sukut varianti): har bir control plane node static
Pod sifatida bitta etcd a’zosini ishga tushiradi; har bir `etcd.yaml` dagi
`--initial-cluster` barcha peer’larni sanab beradi;
`kubeadm join --control-plane` yangi a’zoni siz uchun qo’shadi.

**External**: etcd ajratilgan host’larda, har biri systemd xizmati sifatida;
API server’lar `--etcd-servers=https://etcd1:2379,https://etcd2:2379,https://etcd3:2379`
va etcd CA’si imzolagan mijoz sertifikatlarini oladi. Nosozliklar control
plane’dan mustaqil va etcd host’larini alohida o’lchashingiz mumkin (tez SSD -
etcd kechikishga sezgir).

```bash
# external: API serverning ko'rinishi
grep etcd-servers /etc/kubernetes/manifests/kube-apiserver.yaml
# stacked: a'zoning ko'rinishi
grep initial-cluster /etc/kubernetes/manifests/etcd.yaml
# --initial-cluster=cp1=https://192.168.1.10:2380,cp2=https://192.168.1.11:2380,cp3=https://192.168.1.12:2380
```

## HA bilan o’zgaradigan amallar

- **Backup**: `snapshot save` har qanday sog’lom a’zodan; bitta snapshot -
  butun klasterning holati.
- **Tiklash**: snapshot’ni **har bir** a’zoda o’zining `--name`,
  `--initial-cluster`, `--initial-advertise-peer-urls` va yangi
  `--initial-cluster-token` qiymatlari bilan tiklang, so’ng ularni birga ishga
  tushiring - hujjatlarning "Restoring an etcd cluster" sahifasida aniq
  flaglar bor. Imtihonda klaster xizmati bosqichidagi bitta a’zoli tiklash
  so’raladi.
- **A’zoni almashtirish**: `etcdctl member remove <id>`, so’ng yangi peer URL
  bilan `member add`, so’ng yangi a’zoni `--initial-cluster-state=existing`
  bilan ishga tushiring. Buni qilayotganda klaster hech qachon kvorumdan
  pastga tushmasin.
- **Control plane node qo’shish** (stacked): `kubeadm join --control-plane`
  a’zo qo’shishni o’zi bajaradi.

:::exam-tip
Raqamlar: 3 → 1 tasini yo’qotasiz, 5 → 2 tasini. Xatti-harakat: kvorumdan
past bo’lsa, yozuv yo’q, leader yo’q, API server xato beradi, mavjud Pod’larga
ta’sir qilmaydi. API server’dagi a’zolarni sanab beruvchi flag:
`--etcd-servers`. Leaderni ko’rsatadigan buyruq:
`etcdctl endpoint status --cluster -w table`.
:::

## O’zingizni tekshiring

1. 3 a’zoli etcd’da bitta yozuvni boshidan oxirigacha kuzating: kim nima
   qiladi va mijozga qachon javob beriladi?
2. Beshta a’zo; uchtasi o’chgan. O’qishlar-chi? Yozuvlar-chi? Nega?
3. Nega 4 a’zoli klaster 3 a’zolisidan ko’ra ko’proq mavjud emas?
