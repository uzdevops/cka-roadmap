## API’ga yangi kind o’rgatish

Pod, Deployment, Service - o’rnatilgan kind’lar - har biri API server etcd’da
saqlaydigan va biror yo’l ostida beradigan resurs bo’lib, har birining ular
ustida harakat qiladigan kontrolleri bor. **CustomResourceDefinition** API
serverni o’zgartirmasdan xuddi shu tarzda yangi kind qo’shadi: siz sxemani
tasvirlaysiz, API server `/apis/<your group>/<version>/...`’ni bera boshlaydi
va `kubectl` uning obyektlarini boshqa har qanday obyekt kabi yarata, ola va
o’chira oladi.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: flighttickets.flights.com          # ALBATTA <plural>.<group> bo'lishi shart
spec:
  group: flights.com
  scope: Namespaced                         # yoki Cluster
  names:
    kind: FlightTicket
    singular: flightticket
    plural: flighttickets
    shortNames: [ft]
  versions:
    - name: v1
      served: true
      storage: true                         # aynan bitta versiya storage versiyasi bo'ladi
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                from:   {type: string}
                to:     {type: string}
                number: {type: integer, minimum: 1, maximum: 10}
```

```bash
kubectl apply -f flightticket-crd.yaml
kubectl get crd
kubectl api-resources | grep flight
# flighttickets   ft   flights.com/v1   true   FlightTicket
kubectl explain flightticket.spec           # siz yozgan sxema, explain orqali
```

Endi custom obyektning o’zi:

```yaml
apiVersion: flights.com/v1
kind: FlightTicket
metadata:
  name: my-flight-ticket
spec:
  from: Tashkent
  to: Istanbul
  number: 2
```

```bash
kubectl apply -f ticket.yaml
kubectl get flighttickets        # yoki: kubectl get ft
kubectl describe ft my-flight-ticket
```

Sxema majburiy: `number: 15`’ni API server validatsiya xatosi bilan rad etadi,
xuddi noto’g’ri Pod spec’ini rad etgani kabi.

## CRD nima qilmaydi

Obyektni yaratish uni saqlaydi. **Hech narsa sodir bo’lmaydi.** Hech qanday
chipta bron qilinmaydi, chunki FlightTicket’larni hech kim kuzatmayapti. CRD -
bu ma’lumot turi; xatti-harakat **custom kontroller**dan keladi - bu yangi
kind’ni kuzatib, har bir obyekt ustida harakat qiladigan dastur (odatda
klasterdagi Deployment), xuddi Deployment kontrolleri Deployment’larni
kuzatgani kabi. Bu - keyingi dars; undan keyingisi esa ikkalasini birga
o’raydigan **operator** patterni.

```
CRD (sxema) + custom obyektlar (ma'lumot) + custom kontroller (xatti-harakat) = operator
```

## O’zingiz yozmagan CRD’larni o’qish

Ko’pchilik klasterlarda siz o’rnatgan narsalardan kelgan CRD’lar bor -
cert-manager’ning `Certificate`’i, Prometheus’ning `ServiceMonitor`’i,
Argo’ning `Application`’i, Gateway API’ning `HTTPRoute`’i. Ular nimaligini
o’sha buyruqlarning o’zi aytadi:

```bash
kubectl get crd
kubectl get crd certificates.cert-manager.io -o yaml | grep -A20 openAPIV3Schema
kubectl explain certificate.spec --recursive
kubectl get certificates -A
```

:::exam-tip
Imtihondagi CRD topshiriqlari shunday: "berilgan spec bo’yicha shu CRD’ni
yarating / shu custom kind’ning obyektini yarating / custom obyektlarni
ro’yxatlang". Tekshiriladigan joylar: `metadata.name` `<plural>.<group>`
ko’rinishida; `scope` topshiriqqa mos; aynan bitta versiyada `storage: true`;
obyektning `apiVersion`’i `<group>/<version>`. Keyin
`kubectl api-resources | grep <group>` API uni bilishini isbotlaydi.
:::

## O’chirish

```bash
kubectl delete ft my-flight-ticket
kubectl delete crd flighttickets.flights.com      # u bilan birga HAR BIR FlightTicket obyekti o'chadi
```

CRD’ni o’chirish uning barcha obyektlarini o’chiradi. Operator ulardan
foydalanayotgan klasterda bu - uzilish; avval operatorni o’chirib tashlang.

## O’zingizni tekshiring

1. CRD yaratish sizga nimani beradi va nimani bermaydi?
2. CRD’ning `metadata.name`’i qanday bo’lishi shart va uning versiyalaridan
   biri nimani o’rnatishi kerak?
3. Custom obyekt yaratdingiz va "hech narsa bo’lmayapti". Bu xatomi?
