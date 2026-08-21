## Nega Pod’lar oldida biror narsa turishi kerak

Pod IP’lari o’zgaradi. Deployment har safar rollout qilganda, node har safar
bo’shatilganda ilovangiz ortidagi Pod’lar yangi manzilli yangi Pod’lar
bo’ladi. Hech bir narsani Pod IP’siga murojaat qiladigan qilib sozlab, uni
ishlaydigan holda qoldirib bo’lmaydi. **Service** - ana shu barqaror narsa:
bitta nom, bitta virtual IP va Pod’lar kelib-ketishi bilan backend’lar
ro’yxatini dolzarb saqlab turadigan selector.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: ClusterIP          # sukut bo'yicha; keyingi darsda ko'riladi
  selector:
    app: web
  ports:
    - port: 80             # Service'ning porti
      targetPort: 8080     # konteynerning porti
      protocol: TCP
```

Ishni uchta maydon bajaradi:

- **selector** - uning ortida qaysi Pod’lar turishi. Endpoint kontrolleri buni
  mos keluvchi Pod’larning IP va portlarini sanab beruvchi **EndpointSlice**ga
  aylantiradi.
- **port** - klientlar Service’da nimaga ulanishi.
- **targetPort** - Pod aslida nimani tinglashi. Tushirib qoldirilsa, u `port`
  ga teng bo’ladi. U **nom** ham bo’lishi mumkin: nomlangan `containerPort` ga
  mos keladi va bu Service’ga tegmasdan konteyner portini o’zgartirish
  imkonini beradi.

## Uchta tur

| Tur | Qayerdan yetib boriladi | Nima oladi |
|---|---|---|
| **ClusterIP** | faqat klaster ichidan | service CIDR’dan virtual IP |
| **NodePort** | har bir node’ning IP’sidan, yuqori portda | ClusterIP **plyus** har bir node’da ochiladigan 30000-32767 oralig’idagi port |
| **LoadBalancer** | tashqi dunyodan, cloud yuk muvozanatlagichi orqali | NodePort **plyus** cloud ajratgan tashqi IP |

Ular ichma-ich joylashgan: LoadBalancer - bu NodePort, NodePort esa - bu
ClusterIP. Bu dars NodePort’ni ko’rib chiqadi; keyingi ikkitasi ClusterIP’ni
chuqurroq va LoadBalancer’ni yoritadi.

## NodePort qadam-baqadam

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-np
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080     # ixtiyoriy; qoldirsangiz, oraliqdan bittasi tanlanadi
```

Bitta spec’da uchta port bor va nomlar hammani bir marta chalkashtiradi:

```
klient ──▶ <any node IP>:30080 (nodePort) ──▶ 10.96.x.x:80 (port, ClusterIP) ──▶ 10.244.x.x:8080 (targetPort, Pod)
```

**Yagona majburiysi - `port`**. `targetPort` sukut bo’yicha `port` ga teng
bo’ladi, `nodePort` esa yozilmasa ajratiladi.

```bash
kubectl expose deployment web --name=web-np --type=NodePort --port=80 --target-port=8080
kubectl get svc web-np
# NAME     TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# web-np   NodePort   10.96.14.201   <none>        80:31234/TCP   3s
curl http://<node-ip>:31234
```

NodePort **har bir** node’da ochiladi, hatto Pod’larning birortasi ishlamayotgan
node’da ham - kube-proxy uni klaster tarmog’i orqali uzatadi. Bu qulay va
bir oz isrofgarchilik; shu sababli ham NodePort’lar development uchun va
o’zingizning yuk muvozanatlagichingiz ortida turish uchun, production
ilovalarini bittalab ochish uchun emas.

:::exam-tip
`kubectl expose` `nodePort` ni belgilay olmaydi. Topshiriqda aniq node port
so’ralsa: `kubectl expose ... --type=NodePort --dry-run=client -o yaml > svc.yaml`,
port yozuvi ostiga `nodePort: 30080` qo’shing, so’ng `kubectl apply -f svc.yaml`.
:::

## Service "ishlamaganda"

```bash
kubectl get endpoints web          # or: kubectl get endpointslices -l kubernetes.io/service-name=web
kubectl describe svc web | grep -E "Selector|Endpoints|Port"
kubectl get pods -l app=web -o wide
```

| Ko’rayotganingiz | Nimani anglatadi |
|---|---|
| `Endpoints: <none>` | selector hech qaysi Pod’ga mos kelmaydi (label’da xato) yoki Pod’lar Ready emas |
| endpoint’lar ko’rinadi, lekin ulanish rad etiladi | `targetPort` konteyner tinglayotgan port emas |
| klaster ichidan ishlaydi, tashqaridan ishlamaydi | bu ClusterIP, sizga esa NodePort/LoadBalancer kerak edi |
| nom aniqlanmaydi | CoreDNS, yoki siz boshqa namespace’dasiz va qisqa nomdan foydalandingiz |

:::tip
Readiness probe’dan o’tmagan Pod’lar endpoint’lardan chiqarib tashlanadi. Pod’lar
sog’lom ko’rinib turib endpoint’lari bo’sh bo’lgan Service odatda "Ready emas"
degani - selector’dan oldin `kubectl get pods` dagi READY ustunini tekshiring.
:::

## O’zingizni tekshiring

1. NodePort Service’dagi uchta portni va ularning har biri nima ekanini ayting.
2. Ulardan qaysi biri majburiy va qolganlari sukut bo’yicha nimaga teng bo’ladi?
3. Uchta Pod Running bo’lsa ham, `kubectl get endpoints web` `<none>` chiqarmoqda.
   Ikkita ehtimoliy sabab nima?
