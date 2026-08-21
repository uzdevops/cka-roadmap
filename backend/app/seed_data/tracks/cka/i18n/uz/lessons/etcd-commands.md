## API versiyasi - bir marta va butunlay

etcd’ning ikkita klient API’si bo’lgan. Kubernetes **v3**dan foydalanadi va
zamonaviy `etcdctl` binary’lari sukut bo’yicha v3’ni oladi - lekin eskilari
sukut bo’yicha v2’ni olardi va ikkalasi bir-biriga mos emas. Shuning uchun har
bir qo’llanmada har bir buyruq oldida `ETCDCTL_API=3` ni ko’rasiz: u sizga hech
narsaga tushmaydi va "nega bu ishlamayapti" degan butun bir muammolar sinfini
yo’q qiladi.

```bash
etcdctl version
# etcdctl version: 3.5.x
# API version: 3.5
```

Agar `etcdctl` PATH’ingizda bo’lmasa, u etcd konteyneri ichida turadi:

```bash
kubectl exec -n kube-system etcd-controlplane -- etcdctl version
```

## Yodlashga arziydigan buyruqlar

Oldingi darsdagidek ulanish flaglari export qilingan holda:

```bash
# --- sog'liq va a'zolik ----------------------------------------------
etcdctl endpoint health
etcdctl endpoint status --write-out=table
etcdctl member list --write-out=table

# --- o'qish ----------------------------------------------------------
etcdctl get /registry/namespaces --prefix --keys-only
etcdctl get /registry/secrets/default/mysecret          # xom qiymat (protobuf)
etcdctl get /registry/secrets/default/mysecret | hexdump -C | head
etcdctl get / --prefix --keys-only | wc -l               # klaster nechta obyekt saqlaydi

# --- snapshot --------------------------------------------------------
etcdctl snapshot save /opt/snapshot.db
etcdctl snapshot status /opt/snapshot.db --write-out=table   # 3.5+ da etcdutl snapshot status

# --- xavflilari, to'liqlik uchun -------------------------------------
etcdctl put /some/key value
etcdctl del /some/key
etcdctl compact <revision> ; etcdctl defrag
```

:::warning
`/registry/...` kalitlariga `put` va `del` API serverni chetlab o’tadi -
validatsiya yo’q, admission yo’q, RBAC yo’q, audit log yo’q. Kubernetes
klasterida buni qilishning biror oqlangan sababi yo’q. Bu fe’llar borligini
biling; ularni klaster ma’lumotlariga ishlatmang.
:::

## Secret’ni to’g’ridan-to’g’ri etcd’dan o’qish

Bu - "Secret’lar faqat base64" degan gapni joyiga tushiradigan namoyish:

```bash
kubectl create secret generic demo --from-literal=password=hunter2
etcdctl get /registry/secrets/default/demo | hexdump -C | grep -A1 hunter
```

Parol o’sha yerda, ochiq holda, har bir control plane node diskida turibdi.
Yechim - encryption at rest - ilova hayotiy tsikli bosqichidagi alohida dars;
hozircha xulosa shuki, **etcd diski va uning snapshot’lari barcha Secret’lar
birgalikda qanchalik nozik bo’lsa, shunchalik nozik**.

## snapshot save va snapshot restore

etcd 3.5 dan boshlab backup’ning ikki yarmi turli binary’larda yashaydi:

| Amal | Vosita | Ishlayotgan etcd kerakmi? |
|---|---|---|
| snapshot olish | `etcdctl snapshot save` | ha - u jonli a’zodan so’raydi |
| snapshot’ni tekshirish | `etcdutl snapshot status` | yo’q |
| snapshot’ni tiklash | `etcdutl snapshot restore` | yo’q - u yangi ma’lumotlar katalogini yozadi |

`etcdctl snapshot restore` 3.5 da hali ham deprecation ogohlantirishi bilan
ishlaydi va imtihon ikkalasini ham qabul qiladi. Tiklash uchun `etcdutl`
ishlating, shunda odatingiz zamonaviysi bo’ladi.

```bash
etcdutl snapshot restore /opt/snapshot.db --data-dir /var/lib/etcd-from-backup
```

Keyin nima bo’lishi - etcd yangi katalogdan ishga tushishi uchun static Pod
manifestini tahrirlash - klaster xizmat ko’rsatish bosqichidagi backup va
tiklash darsi.

:::exam-tip
Snapshot **save** uchun endpoint va uchta TLS flag kerak (u serverga murojaat
qiladi). **Restore** uchun kerak emas - u faqat faylni o’qiydi va katalog
yozadi. Nomzodlar hech qachon kerak bo’lmagan sertifikat flaglarini restore’ga
qo’shib, daqiqalarni yo’qotadi.
:::

## O’zingizni tekshiring

1. Nega har bir qo’llanma `ETCDCTL_API=3` bilan boshlanadi va uni qachon tashlab
   yuborish mumkin?
2. `snapshot save` va `snapshot restore` dan qaysi biriga `--cacert`, `--cert`
   va `--key` flaglari kerak va nega?
3. Secret’ni `etcdctl get` bilan o’qish Kubernetes sukut bo’yicha Secret’larni
   qanday saqlashi haqida nimani isbotlaydi?
