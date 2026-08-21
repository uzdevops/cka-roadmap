## Ikki vosita, ataylab ajratilgan

etcd 3.5 gacha `etcdctl` hamma ishni qilardi. 3.5 dan boshlab loyiha **fayllar**
ustida ishlaydigan buyruqlarni - snapshot’ni tiklash, uni tekshirish,
ma’lumotlar katalogini offline defragmentatsiya qilish - ikkinchi binary’ga,
**`etcdutl`** ga ajratdi va `etcdctl`’da **ishlab turgan server** bilan
gaplashadigan buyruqlarni qoldirdi. Sababi: tiklash hech qachon tasodifan
jonli klasterga yo’naltirilmasligi kerak, tarmoq ulanishini ocha olmaydigan
vosita esa buni qila olmaydi.

| Vazifa | Vosita | Serverga murojaat qiladimi? |
|---|---|---|
| `snapshot save` | `etcdctl` | ha - endpoint + TLS kerak |
| `endpoint health` / `endpoint status` / `member list` | `etcdctl` | ha |
| `get` / `put` / `del` | `etcdctl` | ha |
| `snapshot restore` | **`etcdutl`** | yo’q - faylni o’qiydi, katalog yozadi |
| `snapshot status` | **`etcdutl`** | yo’q |
| `defrag` (offline, ma’lumotlar katalogida) | **`etcdutl`** | yo’q |

`etcdctl snapshot restore` va `etcdctl snapshot status` 3.5 da hali ham
deprecated alias sifatida mavjud va ogohlantirish chiqaradi. Ular 3.6 da olib
tashlangan. Ikkalasi uchun `etcdutl` yozing - shunda odatingiz kelajakka mos
bo’ladi.

## Binary’lar qayerda

kubeadm control plane’da ular sukut bo’yicha host’da emas, **etcd konteyneri
ichida** turadi:

```bash
kubectl exec -n kube-system etcd-controlplane -- etcdctl version
kubectl exec -n kube-system etcd-controlplane -- etcdutl version
```

Snapshot uchun bu yetarli - ichiga exec qiling, ishga tushiring, fayl
konteyner fayl tizimi ichiga tushadi; uni node’ga chiqarish uchun hostPath
mount bo’lgan yo’lga yozing (`/var/lib/etcd` shundaylardan biri, yoki
`/opt`’ni qo’shing). Tiklash uchun esa binary **host’da** bo’lgani ma’qul, chunki siz
host’da yangi katalog yozasiz va host faylini tahrirlaysiz:

```bash
# binary'larni image'dan bir marta nusxalab oling
kubectl cp -n kube-system etcd-controlplane:/usr/local/bin/etcdutl /usr/local/bin/etcdutl
chmod +x /usr/local/bin/etcdutl
# yoki: github.com/etcd-io/etcd dan mos keladigan release tarball'ini yuklab oling
```

Imtihon muhitlarida odatda ikkalasi ham control plane node’da mavjud bo’ladi;
birinchi tekshiradigan narsangiz - `which etcdctl etcdutl`.

## Versiya muhim

etcd serveriga mos keladigan vosita versiyasidan foydalaning:

```bash
kubectl exec -n kube-system etcd-controlplane -- etcd --version
etcdctl version
```

3.5 server olgan snapshot 3.5 `etcdutl` bilan muammosiz tiklanadi. 3.4
`etcdctl`’ni 3.5 serverga qarshi aralashtirish `get`/`save` uchun asosan
ishlaydi, lekin xato xabarlari chalkash bo’lib qoladi; ularni moslashtirish
bitta noma’lumni olib tashlaydi.

## Buyruqlar yonma-yon

```bash
# --- etcdctl: jonli server kerak bo'ladigan hamma narsa ----------------
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key

etcdctl endpoint health
etcdctl endpoint status --write-out=table
etcdctl member list --write-out=table
etcdctl snapshot save /opt/snap.db

# --- etcdutl: fayllar ustida ishlaydigan hamma narsa -------------------
etcdutl snapshot status /opt/snap.db --write-out=table
etcdutl snapshot restore /opt/snap.db --data-dir /var/lib/etcd-from-backup
etcdutl defrag --data-dir /var/lib/etcd            # faqat etcd to'xtatilgan holda
```

Muhit o’zgaruvchilariga e’tibor bering: `etcdctl` har bir flag uchun
`ETCDCTL_*`’ni o’qiydi, shuning uchun ularni har bir shell’da bir marta export
qilsangiz, keyingi har bir buyruq qisqa bo’ladi. Ular `etcdutl`’ga ta’sir
qilmaydi - unga bular kerak emas.

:::exam-tip
Agar topshiriqda "tiklash uchun etcdctl ishlating" deyilgan bo’lsa - shunday
qiling, u ogohlantirish bilan ishlaydi. Agar hech narsa deyilmagan bo’lsa,
`etcdutl` ishlating. Har ikki holatda ham tiklash **hech qanday** endpoint va
**hech qanday** sertifikat flagini olmaydi; ularni qo’shish `etcdctl`’da
zararsiz, `etcdutl`’da esa xato. Ikkita ustunni yodda tuting: tarmoq →
etcdctl, fayl → etcdutl.
:::

## O’zingizni tekshiring

1. Nega etcd loyihasi `snapshot restore`’ni `etcdctl`’dan chiqarib yubordi?
2. Siz `ETCDCTL_*` o’zgaruvchilarini export qildingiz. `etcdutl snapshot
   restore` ulardan foydalanadimi?
3. Agar `etcdutl` host PATH’ida bo’lmasa, uni kubeadm control plane’da
   qayerdan topasiz?
