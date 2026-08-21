## Har bir manifestda bo’ladigan to’rt maydon

Siz yozadigan har bir Kubernetes obyektining skeleti bir xil:

```yaml
apiVersion:   # bu kind qaysi API guruhi va versiyasidan kelgani
kind:         # bu nima
metadata:     # nom, namespace, label'lar, annotatsiyalar
spec:         # siz nima xohlayotganingiz
```

Beshinchisini, `status`’ni, siz emas, klaster yozadi. Pod uchun:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels:
    app: web
    tier: frontend
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

Uni yuqoridan pastga o’qing: bu core API’dan (`v1`) kelgan, `web` deb
nomlangan, ikkita label ko’tarib yurgan `Pod` va uning kutilgan holati - o’sha
image’dan olingan `nginx` nomli bitta konteyner. `containers` maydoni -
**ro’yxat**; o’sha chiziqcha bezak emas, aynan u Pod’ga bittadan ortiq
konteyner ushlash imkonini beradi.

## Maydon nomlari qayerdan keladi

Siz ularni yodlamaysiz; ularni qidirib topasiz:

```bash
kubectl explain pod.spec                       # spec'ning har bir maydoni, turlari bilan
kubectl explain pod.spec.containers            # konteyner obyekti
kubectl explain pod.spec.containers.resources --recursive
```

Odamlar `apiVersion`’da xato qiladi. Taxminiy qoida:

| Kind | apiVersion |
|---|---|
| Pod, Service, ConfigMap, Secret, Namespace, Node, PersistentVolume(Claim), ServiceAccount | `v1` |
| Deployment, ReplicaSet, DaemonSet, StatefulSet | `apps/v1` |
| Job, CronJob | `batch/v1` |
| Ingress, NetworkPolicy | `networking.k8s.io/v1` |
| Role, RoleBinding, ClusterRole, ClusterRoleBinding | `rbac.authorization.k8s.io/v1` |
| HorizontalPodAutoscaler | `autoscaling/v2` |

`kubectl api-resources` klasteringiz uchun butun jadvalni chop etadi.

## Tishlaydigan YAML qoidalari

- **Indentatsiya - bu tuzilmaning o’zi.** Har bosqichga ikkita bo’sh joy,
  faqat bo’sh joy, hech qachon tab emas. Bir bo’sh joyga adashgan kalit
  farzand emas, birodar bo’lib qoladi va xato xabari buni aytmaydi.
- **Ro’yxatlar `- ` bilan boshlanadi.** `containers:` map’lar ro’yxatini
  oladi; har bir `- name:` yangi konteynerni boshlaydi.
- **Boshqa narsaga o’xshab ko’rinadigan satrlar.** `"80"` - satr, `80` - son;
  `containerPort` sonni kutadi, env ichidagi `value` esa satrni.
  `yes`/`no`/`on`/`off` YAML 1.1 da mantiqiy qiymatlar - ularni tirnoqqa
  oling.
- **`---` hujjatlarni ajratadi**, shuning uchun bitta fayl Pod va uning
  Service’ini birga saqlashi mumkin.

:::tip
Skeletlarni qo’lda yozmang. `kubectl run web --image=nginx --dry-run=client -o
yaml > pod.yaml` sizga tahrirlash uchun tayyor, `apiVersion`i va indentatsiyasi
allaqachon to’g’ri fayl beradi. Bu - imtihondagi eng foydali odat.
:::

## Fayldan klasterga va qaytib

```bash
kubectl apply -f pod.yaml          # yaratadi yoki yangilaydi
kubectl create -f pod.yaml         # faqat yaratadi - mavjud bo'lsa xato beradi
kubectl get pod web -o yaml        # obyekt klasterda qanday saqlansa, status bilan
kubectl get pod web -o yaml > current.yaml   # tahrirlash uchun qaytarib olish
kubectl delete -f pod.yaml
```

`get -o yaml` qaytargan narsada siz yozganingizdan ko’prog’i bor - to’ldirilgan
sukut qiymatlari (`restartPolicy: Always`, `dnsPolicy: ClusterFirst`, service
account, `status` bloki). Bu normal; ularni klaster qo’shgan.

:::exam-tip
Pod’ning ko’p maydonlari yaratilgandan keyin o’zgarmas bo’ladi (image - joyida
o’zgartira oladigan sanoqli maydonlardan biri). Agar `kubectl apply` "field is
immutable" deb rad etsa, yo’l - `kubectl replace --force -f pod.yaml` - bitta
qadamda o’chirib qayta yaratish - va o’sha fayl sizga kerak bo’lgan hamma
narsani o’z ichiga olishi shart.
:::

## O’zingizni tekshiring

1. Har bir manifestda qaysi to’rtta yuqori darajali maydon bo’ladi va
   beshinchisini nega hech qachon yozmasligingiz kerak?
2. Deployment, Job va Ingress uchun `apiVersion`’ni yoddan yozing.
3. `kubectl apply` maydon o’zgarmas deb aytmoqda. Bir qatorli yechim nima va u
   ishlab turgan Pod’ga nima qiladi?
