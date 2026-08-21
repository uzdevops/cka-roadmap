## Nimalarni backup qilish kerak

kubeadm klasterining holati uchta joyda turadi:

| Nima | Qayerda | Qanday saqlanadi |
|---|---|---|
| har bir obyekt (klasterning xotirasi) | etcd | `etcdctl snapshot save` |
| control plane’ning o’z ta’rifi | `/etc/kubernetes/manifests`, `/etc/kubernetes/pki`, `/etc/kubernetes/*.conf` | katalogni nusxalash |
| siz e’lon qilgan niyat | Git’dagi manifestlar | Git |

Ba’zi jamoalar "hammasi Git’da va `kubectl apply` uni qayta quradi" degan
fikrga tayanib etcd backup’ini o’tkazib yuboradi. Qayta qurmaydi: qo’lda
yaratilgan Secret’lar, klaster bergan sertifikatlar, Lease’lar, operator yozgan
hamma narsa - bularning hech biri Git’da yo’q. **etcd’ni backup qiling.**

## Snapshot olish

```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /opt/snapshot-pre-boot.db

# Snapshot saved at /opt/snapshot-pre-boot.db
etcdutl snapshot status /opt/snapshot-pre-boot.db --write-out=table    # hash, revision, kalitlar, hajm
```

Har safar to’rtta flag: endpoint va uchta TLS fayli. Ularni
`/etc/kubernetes/manifests/etcd.yaml` dan o’qib olasiz
(`--listen-client-urls`, `--trusted-ca-file`, `--cert-file`, `--key-file`).
Snapshot - bitta fayl; u butun klaster, Secret’lari bilan birga, shuning uchun
unga shunday munosabatda bo’ling.

:::exam-tip
Topshiriq sizga yo’llarni beradi - *ulardan foydalaning*. U 127.0.0.1
bo’lmagan endpoint ham berishi mumkin (tashqi etcd host’i). Agar topshiriq
matnida flaglar bo’lsa, ularni yoddan yozmang; ko’chiring. Imtihonda
snapshot’ning eng keng tarqalgan nosozligi - boshqa klaster odati bo’yicha
yozilgan sertifikat yo’li.
:::

## Tiklash

Tiklash snapshot’ni "etcd’ga yuklamaydi". U snapshot’dan **butunlay yangi
ma’lumotlar katalogini yozadi**, keyin siz etcd’ga eski katalog o’rniga o’sha
katalogdan ishga tushishni aytasiz.

```bash
etcdutl snapshot restore /opt/snapshot-pre-boot.db --data-dir /var/lib/etcd-from-backup
# (etcdctl snapshot restore 3.5 da hali ishlaydi, deprecation ogohlantirishi bilan)
```

Endpoint yo’q, sertifikat yo’q: bu fayldan katalogga amal, etcd ishlab turishi
shart emas va u maqsad katalogga allaqachon egalik qilayotgan bo’lmasligi
kerak.

So’ng etcd static Pod’ini yangi katalogga yo’naltiring:

```yaml
# /etc/kubernetes/manifests/etcd.yaml
volumes:
  - hostPath:
      path: /var/lib/etcd-from-backup     # <- oldin /var/lib/etcd edi
      type: DirectoryOrCreate
    name: etcd-data
```

Konteynerning `--data-dir=/var/lib/etcd` flagi va uning mount yo’li o’z
holicha qolishi mumkin: o’zgargani hostPath, shuning uchun konteyner ichidagi
o’sha yo’l endi tiklangan ma’lumotlarga bog’lanadi. (`--data-dir` ni ham
o’zgartirsa bo’ladi, faqat volumeMount unga mos kelsin.)

Faylni saqlang; kubelet etcd’ni yangi katalogdan qayta ishga tushiradi; ~30 s
dan keyin API server qayta ulanadi va snapshot’dagi obyektlar joyiga qaytadi.

```bash
kubectl get pods -n kube-system | grep etcd       # Running
kubectl get deploy,svc -A                          # yo'qotgan narsalaringiz qaytdi
```

:::warning
Tiklash klaster holatini snapshot holatiga almashtiradi. Snapshot’dan keyin
yaratilgan hamma narsa yo’qoladi. Keyin kontrollerlar haqiqatni unga
moslashtiradi: node’larda mavjud, lekin tiklangan etcd’da yo’q Pod’lar
tozalanadi, snapshot’da bor, lekin node’larda yo’q Pod’lar qayta yaratiladi.
O’zingiz mo’ljallagan snapshot’ga tiklang.
:::

## Tashqi etcd

Agar etcd static Pod bo’lmasa va o’z host(lar)ida ishlasa:

```bash
# aniqlang: etcd Pod bormi?
kubectl get pods -n kube-system | grep etcd             # yo'q -> tashqi
ps -ef | grep etcd                                       # etcd host'ida
cat /etc/systemd/system/etcd.service                     # flaglar va data dir shu yerda
```

Snapshot buyrug’i o’sha-o’sha (o’sha host’ning endpoint va sertifikatlari
bilan); tiklash uchun systemd unit’dagi `--data-dir` ni o’zgartiring (va yangi
katalogga `chown etcd:etcd` qiling), so’ng `systemctl daemon-reload &&
systemctl restart etcd`.

## Nazorat ro’yxati

```
save:     endpoint + 3 certs + snapshot save <file>
restore:  snapshot restore <file> --data-dir <new dir>
          edit etcd.yaml hostPath -> <new dir>       (or the systemd unit for external etcd)
          wait, kubectl get pods -n kube-system, verify the objects
```

## O’zingizni tekshiring

1. `snapshot save` va `snapshot restore` dan qaysi biriga TLS flaglari kerak
   va nega?
2. Tiklashdan keyin qaysi bitta tahrir klasterni tiklangan ma’lumotlardan
   haqiqatan foydalanishga majbur qiladi va etcd’ni nima qayta ishga
   tushiradi?
3. Nega "bizda hammasi Git’da" etcd backup’ining o’rnini bosa olmaydi?
