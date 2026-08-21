## Muammoni ko’rish

```bash
kubectl create secret generic demo --from-literal=password=hunter2
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/demo | hexdump -C | grep -A1 hunter
```

Mana u - control plane diskida va siz oladigan har bir etcd snapshot’ida
o’qib bo’ladigan holda turibdi. **Diskda shifrlash** (encryption at rest) API
serverni tanlangan resurslarni etcd’ga yozishdan oldin shifrlashga va
o’qishda deshifrlashga majbur qiladi; shundan keyin etcd va uning backup’lari
shifrlangan matnni saqlaydi.

## EncryptionConfiguration

```yaml
# /etc/kubernetes/enc/enc.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps            # ixtiyoriy, ularni ham xohlasangiz
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64 of 32 random bytes>
      - identity: {}          # eski ma'lumotni O'QISH uchun ochiq matnga qaytish
```

```bash
head -c 32 /dev/urandom | base64        # kalit
```

Fayl qoidalari:

- `resources` nimani shifrlashni sanaydi; `providers` esa *qanday*
  shifrlashni, **tartib bilan** sanaydi.
- **Yozish uchun birinchi provider ishlatiladi**. O’qish uchun esa har bir
  provider tartib bo’yicha sinab ko’riladi - aynan shu tufayli eski ochiq
  matnli obyektlar o’qishga yaroqli qoladi, yangi yozuvlar esa shifrlanadi.
- `identity` "shifrlash yo’q" degani. U birinchi turganda hech narsa
  shifrlanmaydi. Oxirida turganda esa oldindan mavjud ochiq matnni o’qish
  uchun zaxira variant bo’ladi.

| Provider | Izohlar |
|---|---|
| `identity` | yo’q |
| `aescbc` | hujjatlar ko’rsatadigani; yaroqli |
| `aesgcm` | tezroq; har ~200k yozuvdan keyin kalit almashtirilishi shart |
| `secretbox` | XSalsa20/Poly1305, kuchli |
| `kms` | tashqi KMS bilan konvert shifrlash - production javobi |

## Uni API serverga ulash

API server faylni flag orqali o’qiydi, shuning uchun u static Pod’ga
**mount** qilinishi kerak:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
    command:
      - kube-apiserver
      - --encryption-provider-config=/etc/kubernetes/enc/enc.yaml
    volumeMounts:
      - name: enc
        mountPath: /etc/kubernetes/enc
        readOnly: true
volumes:
  - name: enc
    hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
```

Saqlang; kubelet API serverni qayta ishga tushiradi; kuting; keyin
`kubectl get --raw /healthz`.

:::warning
Endi etcd snapshot’i bilan har bir Secret orasida turgan yagona narsa -
shifrlash kaliti. **Kalitni snapshot’lardan alohida backup qiling** va
`/etc/kubernetes/enc`’ni yoping (`chmod 600`). Kalitni yo’qotsangiz, har bir
shifrlangan obyekt butunlay yo’qoladi.
:::

## Buni isbotlash va oldin yozilganini shifrlash

```bash
kubectl create secret generic demo2 --from-literal=password=hunter3
etcdctl ... get /registry/secrets/default/demo2 | hexdump -C | head -3
# 00000000  2f 72 65 67 69 73 74 72 79 2f 73 65 63 72 65 74  |/registry/secret|
# 00000010  ... 6b 38 73 3a 65 6e 63 3a 61 65 73 63 62 63 3a  |...k8s:enc:aescbc:|
```

`k8s:enc:aescbc:v1:key1:` va ketidan shovqin - demak shifrlangan. O’zgarishdan
*oldin* yozilgan obyektlar qayta yozilmaguncha ochiq matn bo’lib qoladi:

```bash
kubectl get secrets -A -o json | kubectl replace -f -      # har bir Secret qayta yoziladi -> qayta shifrlanadi
```

Kalit almashtirish ham xuddi shu g’oya: yangi kalitni ro’yxatda **birinchi**
qilib qo’shing, eskisini ikkinchi qoldiring, qayta ishga tushiring,
yuqoridagi replace’ni bajaring, keyin eski kalitni olib tashlang.

:::exam-tip
"Encrypting Confidential Data at Rest" hujjat sahifasida butun ketma-ketlik
bor - konfiguratsiya fayli, flag, volume mount va `replace` buyrug’i. Bu -
joyini bilib qo’yishga arziydigan sahifalardan biri, chunki topshiriq deyarli
butunlay "qadamlarni xatosiz bajarish"dan iborat. Qimmatga tushadigan ikki
xato: volume mount’ni unutish (API server crash-loop’ga tushadi,
`no such file`) va `identity`’ni birinchi qo’yish (hech narsa shifrlanmaydi va
tekshiruv ishlamaydi).
:::

## O’zingizni tekshiring

1. `providers` ro’yxatida qaysi yozuv yozish uchun, qaysilari o’qish uchun
   ishlatiladi?
2. Shifrlashni sozladingiz va etcd’dagi *eski* Secret’ni tekshirdingiz - u
   hamon ochiq matn. Nega, va buni qaysi buyruq tuzatadi?
3. Diskda shifrlash yoqilgach, etcd snapshot’laridan alohida nimani backup
   qilishingiz kerak - va nega aynan alohida?
