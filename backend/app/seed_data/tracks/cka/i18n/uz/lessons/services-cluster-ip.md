## Sukut bo’yicha tur va eng ko’p ishlatiladigani

ClusterIP Service - bu ilovaning qismlari klaster ichida bir-birini topish
usuli: front end `api` bilan gaplashadi, API `db` bilan gaplashadi va
ularning hech biri bugun bu nomlar ortida qaysi Pod’lar turganini bilmaydi
ham, bilishi ham shart emas. Bu sukut bo’yicha `type`, shuning uchun `type`
umuman yozilmagan Service - ClusterIP.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl expose deployment api --port=80 --target-port=8080
kubectl get svc api
# NAME   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
# api    ClusterIP   10.96.201.77   <none>        80/TCP    2s
```

## Bu IP aslida nima

ClusterIP **service CIDR** dan olinadi (API server’dagi
`--service-cluster-ip-range`, kubeadm’da sukut bo’yicha `10.96.0.0/12`). Bu
virtual IP: uni hech bir interfeys ushlab turmaydi, unga hech narsa ping
qilmaydi. kube-proxy har bir node’ni shunday sozlaydiki, o’sha IP *ga*
ketayotgan paket endpoint’lardan biriga qayta yoziladi. U Service’ning butun
umri davomida o’zgarmaydi - butun gap ham shunda.

```bash
kubectl get svc -A | head           # kubernetes, kube-dns va sizniki - hammasi bitta oraliqdan
```

:::note
Oraliqdagi birinchi manzil, `10.96.0.1`, doim `default` dagi `kubernetes`
Service’i bo’ladi: API server’ning o’zi, Pod’larga ClusterIP sifatida
ochilgan. `kube-dns` Service’i esa an’anaviy ravishda `10.96.0.10`.
:::

## Unga nom orqali murojaat qilish

Har bir Service CoreDNS’dan DNS nom oladi:

```
<service>.<namespace>.svc.cluster.local
```

**Xuddi shu** namespace’dagi Pod’dan qisqa nom ishlaydi; boshqa namespace’dan
esa kamida `<service>.<namespace>` kerak bo’ladi:

```bash
kubectl run t --rm -it --image=busybox -- sh
/ # wget -qO- api            # bir xil namespace
/ # wget -qO- api.payroll    # `payroll` namespace'idagi `api` Service'i
/ # nslookup api.payroll.svc.cluster.local
```

## Bir nechta port va nomlangan portlar

```yaml
spec:
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: http       # containerPort'ning nomi
    - name: metrics
      port: 9090
      targetPort: 9090
```

Bittadan ortiq port bo’lsa, har biriga `name` kerak. Nomlangan `targetPort`
Deployment’ga Service’ni o’zgartirmasdan konteyner portini ko’chirish imkonini
beradi.

## Headless: IP’siz ClusterIP

```yaml
spec:
  clusterIP: None
  selector:
    app: db
```

`clusterIP: None` **headless** Service yasaydi: virtual IP yo’q, yuk
muvozanatlash yo’q. DNS nom to’g’ridan-to’g’ri **Pod IP’lariga** aylanadi.
StatefulSet’lar shundan foydalanadi, shunda har bir replika o’z barqaror
nomini oladi (`db-0.db.payroll.svc.cluster.local`). Agar topshiriqda
"klientlar har bir Pod’ga alohida yeta olishi kerak" deyilsa, javob shu.

## Selector’siz

`selector` ni yozmasangiz, endpoint’lar avtomatik yaratilmaydi - siz
EndpointSlice’ni (yoki eski Endpoints’ni) o’zingiz yaratasiz va uni xohlagan
IP’laringizga qaratasiz. Klaster tashqi ma’lumotlar bazasi uchun barqaror
ichki nomni ana shunday oladi:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: legacy-db
spec:
  ports:
    - port: 5432
---
apiVersion: v1
kind: Endpoints
metadata:
  name: legacy-db           # Service bilan bir xil nom
subsets:
  - addresses: [{ip: 192.168.50.20}]
    ports: [{port: 5432}]
```

:::exam-tip
`kubectl expose` selector’ni nishon obyektning label’laridan quradi va bu
hollarning 99 % ida to’g’ri bo’ladi. Noto’g’ri bo’lganda - topshiriqqa
`app=frontend` kerak, Deployment’ning Pod’larida esa `tier=web` bor -
`--selector=tier=web` qo’shing, aks holda Service endpoint’siz turib qoladi.
:::

## O’zingizni tekshiring

1. Nega ClusterIP’ga ping qila olmaysiz va bu "Service" aslida qayerda
   mavjudligi haqida nima deydi?
2. `default` dagi Pod’dan `payroll` namespace’idagi `api` Service’iga yetadigan
   eng qisqa nom qanday?
3. `clusterIP: None` nimani o’zgartiradi va qaysi workload unga tayanadi?
