## Chop etib bo’lmaydigan narsalar uchun ConfigMap

Secret ConfigMap bilan bir xil shaklga ega - namespace’ga tegishli kalit va
qiymatlar - va xuddi shu uch usulda ishlatiladi. Farq muomalada: qiymatlar
API’da base64 bilan kodlanadi, `kubectl describe` ularni yashiradi, ularni
diskda shifrlash mumkin, RBAC odatda ularni alohida ko’rib chiqadi va kubelet
Secret’ni faqat unga muhtoj Pod ishlaydigan node’larga yuboradi.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  DB_User: cm9vdA==              # base64("root")
  DB_Password: cGFzc3dvcmQxMjM=  # base64("password123")
```

```yaml
stringData:                      # faylda ochiq matn; API uni base64 qilib saqlaydi
  DB_Password: password123
```

`stringData` - faqat yozish uchun qulaylik: siz ochiq matn yozasiz, API server
uni `data` ichiga kodlaydi, obyektni qayta o’qiganingizda esa faqat `data`
ko’rinadi.

## base64 - shifrlash emas

```bash
echo -n 'password123' | base64        # cGFzc3dvcmQxMjM=
echo 'cGFzc3dvcmQxMjM=' | base64 -d   # password123
kubectl get secret db-secret -o jsonpath='{.data.DB_Password}' | base64 -d
```

Secret’ni `get` qila oladigan har kim uni o’qiy oladi. etcd diskiga ega
bo’lgan har kim ham o’qiy oladi, chunki sukut bo’yicha u o’sha yerda ochiq
holda yotadi (etcd darslari buni ko’rsatgan edi). Secret’larni aslida nima
himoya qiladi:

1. **RBAC** - secret’lar ustidan `get`/`list` ruxsatini kerak bo’lmagan
   rollarga bermang; yolg’iz `list` ham har bir qiymatni oshkor qiladi.
2. **Diskda shifrlash** - API serverda `EncryptionConfiguration`, shunda etcd
   shifrlangan matn saqlaydi. Keyingi dars.
3. **Ularni Git’ga solmaslik** - repozitoriydagi `data` bilan Secret manifesti
   - bu sizib chiqish. Bu bo’shliqni Sealed Secrets, SOPS yoki tashqi secrets
   operatori to’ldiradi, lekin bu imtihondan tashqarida.

:::warning
`kubectl create secret ... --from-literal=password=x` parolni shell
tarixingizda qoldiradi. Imtihonda buning ahamiyati yo’q; hayotda esa
`--from-file` yoki keyin o’chirib tashlaydigan `stringData` manifesti.
:::

## Yaratish

```bash
kubectl create secret generic db-secret --from-literal=DB_User=root --from-literal=DB_Password=password123
kubectl create secret generic tls-files --from-file=tls.crt --from-file=tls.key
kubectl create secret tls web-tls --cert=tls.crt --key=tls.key                      # turi kubernetes.io/tls
kubectl create secret docker-registry regcred --docker-server=reg.io --docker-username=u --docker-password=p --docker-email=e@x.io
kubectl get secrets
kubectl describe secret db-secret        # kalitlar va o'lchamlar, qiymatlarsiz
```

| Turi | Nima uchun |
|---|---|
| `Opaque` | har qanday narsa uchun (sukut) |
| `kubernetes.io/tls` | sertifikat va kalit - Ingress TLS |
| `kubernetes.io/dockerconfigjson` | registry hisob ma’lumotlari - `imagePullSecrets` |
| `kubernetes.io/service-account-token` | eski uslubdagi SA token’lari |
| `kubernetes.io/basic-auth`, `ssh-auth` | talab qilinadigan kalitlarga ega konvensiyalar |

## Ishlatish - o’sha uchta shakl

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: DB_Password
envFrom:
  - secretRef:
      name: db-secret
volumes:
  - name: creds
    secret:
      secretName: db-secret
      defaultMode: 0400
containers:
  - volumeMounts:
      - name: creds
        mountPath: /etc/creds
        readOnly: true
```

Mount qilingan Secret’lar node’da **tmpfs**da turadi - hech qachon diskka
yozilmaydi - va ConfigMap’lar kabi joyida yangilanadi (`subPath`’dan
tashqari). env o’zgaruvchilari esa faqat ishga tushishda o’qiladi va muhit
o’zgaruvchilari oson sizib chiqadi (bola jarayonlar, crash dump’lar,
`kubectl describe` uslubidagi vositalar); imkon bo’lsa, volume’ni tanlang.

```bash
kubectl exec app -- cat /etc/creds/DB_Password
kubectl exec app -- env | grep DB_
```

## Yopiq registry’dan image olish

```yaml
spec:
  imagePullSecrets:
    - name: regcred
  containers:
    - image: myregistry.io:5000/app:1.0
```

`docker-registry` turidagi Secret va Pod’dagi `imagePullSecrets` (yoki
ServiceAccount’dagi, shunda uni ishlatadigan har bir Pod meros oladi).
Siz tuzatayotgan alomat - hodisada `unauthorized` bilan kelgan
`ErrImagePull`.

:::exam-tip
`kubectl describe secret` sizga qiymatni ko’rsatmaydi, `kubectl get secret -o yaml`
esa base64 ko’rsatadi. Qiymatni o’qish uchun bitta buyruq -
`kubectl get secret <name> -o jsonpath='{.data.<key>}' | base64 -d`. Nuqtali
kalitlar uchun `{.data.tls\.crt}` kerak.
:::

## O’zingizni tekshiring

1. base64 Secret’ni nimadan himoya qiladi? etcd diskiga ega odamdan uni nima
   himoya qiladi?
2. `db-secret` Secret’ining `DB_Password` kalitini ochiq matnda o’qiydigan
   buyruqni yozing.
3. Pod `ErrImagePull ... unauthorized` bilan ishlamay qoldi. Buni qaysi ikki
   obyekt tuzatadi va murojaat qayerga yoziladi?
