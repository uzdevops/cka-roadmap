## Kalit/qiymat orqali bo’sh bog’lanish

Kubernetes obyektlari bir-biriga ID orqali murojaat qilmaydi. Service ichida
Pod’lar ro’yxati yo’q; unda **selektor** bor va endpoint kontrolleri unga mos
keladigan narsani uzluksiz topib turadi. Aynan shu vositachilik tufayli siz
Service ortidagi har bir Pod’ni Service’ga tegmasdan almashtira olasiz.

```yaml
metadata:
  labels:
    app: web
    tier: frontend
    environment: production
    version: v1.2.3
```

## Label qoidalari

- Kalit: ixtiyoriy DNS-subdomain prefiksi + `/` + nom, masalan
  `example.com/team`. Nom qismi ko’pi bilan 63 belgi.
- Qiymat: ko’pi bilan 63 belgi, harf-raqamlar va `-`, `_`, `.`; bo’sh
  bo’lishi mumkin.
- `kubernetes.io/` va `k8s.io/` prefikslari asosiy komponentlar uchun
  zaxiralangan.

Tavsiya etilgan umumiy label’lar - Helm o’rnatgan har qanday narsada
ularni ko’rasiz:

```yaml
labels:
  app.kubernetes.io/name: web
  app.kubernetes.io/instance: web-prod
  app.kubernetes.io/version: "1.2.3"
  app.kubernetes.io/component: frontend
  app.kubernetes.io/part-of: shop
  app.kubernetes.io/managed-by: helm
```

## Tenglikka asoslangan selektorlar

Oddiy shakl, Service’lar va `kubectl -l` ishlatadi:

```bash
kubectl get pods -l app=web
kubectl get pods -l app=web,tier=frontend        # AND
kubectl get pods -l app!=web
kubectl get pods -l 'app'                        # kalit mavjud, qiymat ixtiyoriy
kubectl get pods -l '!app'                       # kalit mavjud emas
```

```yaml
# Service - faqat tenglikka asoslangan selektorlarni qo'llab-quvvatlaydi
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
    tier: frontend
  ports:
    - port: 80
      targetPort: 8080
```

## To’plamga asoslangan selektorlar

Boyroq shakl; Deployment’lar, ReplicaSet’lar va NetworkPolicy’lar uchun
majburiy:

```bash
kubectl get pods -l 'environment in (production, staging)'
kubectl get pods -l 'tier notin (cache)'
kubectl get pods -l 'app in (web),environment notin (dev)'
```

```yaml
selector:
  matchLabels:
    app: web
  matchExpressions:
    - key: environment
      operator: In
      values: [production, staging]
    - key: tier
      operator: NotIn
      values: [cache]
    - key: track
      operator: Exists
```

Operatorlar: `In`, `NotIn`, `Exists`, `DoesNotExist`. `matchLabels` va
`matchExpressions` ichidagi har bir shart AND orqali birlashtiriladi.

:::warning
Service’ning `spec.selector` maydoni - oddiy map, u `matchExpressions`
ishlata olmaydi. Agar savolda Service uchun to’plamga asoslangan moslik
so’ralsa, javob - shu maqsadda qo’shgan label’ingiz bo’yicha tanlash,
ifodalar yozish emas.
:::

## Label’larni CLI orqali boshqarish

```bash
kubectl label pod web environment=production
kubectl label pod web environment=staging --overwrite
kubectl label pod web environment-                 # o'chirish (oxiridagi tire)
kubectl label pods --all monitored=true
kubectl label nodes cka-worker disktype=ssd

kubectl get pods --show-labels
kubectl get pods -L environment,tier               # label'lar ustun sifatida
```

## Label’lar rejalashtirishni ham boshqaradi

Node label’i va Pod’dagi `nodeSelector` - eng oddiy joylashtirish qoidasi:

```bash
kubectl label nodes cka-worker disktype=ssd
```

```yaml
spec:
  nodeSelector:
    disktype: ssd
```

Bironta node o’sha label’ni ko’tarmaguncha Pod `Pending` holatida qoladi - bu
joylashtirib bo’lmaydigan Pod’larning juda keng tarqalgan sababi.

```bash
kubectl get nodes --show-labels
kubectl describe pod <name> | grep -A5 Events
# 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

## Annotation’lar

Xuddi shu kalit/qiymat shakli, lekin maqsadi teskari: asboblar va odamlar
uchun ixtiyoriy metama’lumot, tanlab bo’l**maydi** va 63 belgi bilan
cheklanmagan.

```yaml
metadata:
  annotations:
    kubernetes.io/change-cause: "upgrade nginx to 1.28"
    nginx.ingress.kubernetes.io/rewrite-target: /
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    description: |
      Owned by the platform team.
      Escalate via #platform-oncall.
```

```bash
kubectl annotate deployment web kubernetes.io/change-cause="bump to 1.28"
kubectl annotate deployment web description-       # o'chirish
```

`kubernetes.io/change-cause` annotation’i rollout tarixidagi CHANGE-CAUSE
ustunini to’ldiradi - savolda muayyan versiyani aniqlash yoki unga rollback
qilish so’ralganda foydali:

```bash
kubectl rollout history deployment/web
# REVISION  CHANGE-CAUSE
# 1         initial deployment
# 2         bump to 1.28
```

:::exam-tip
Ingress xatti-harakati deyarli butunlay annotation’lar orqali sozlanadi
(`nginx.ingress.kubernetes.io/...`). Agar Ingress savolida rewrite, SSL
redirect yoki backend protokoli tilga olinsa, javob - annotation, spec
maydoni emas.
:::

## Label’lar va annotation’lar

| | Label’lar | Annotation’lar |
| --- | --- | --- |
| Maqsadi | Aniqlash va tanlash | Tavsiflash va asboblarni sozlash |
| Tanlab bo’ladimi | Ha | Yo’q |
| Qiymat hajmi | 63 belgi | Amalda cheklanmagan |
| API indekslaydimi | Ha | Yo’q |
| Odatiy qo’llanishi | `app`, `tier`, `environment` | change-cause, ingress konfiguratsiyasi, nazorat summalari |

## O’zingizni tekshiring

1. `environment` `production` yoki `staging`, lekin `tier` `cache` emas
   bo’lgan Pod’larga mos keladigan selektor yozing.
2. Nega Service `matchExpressions` ishlata olmaydi?
3. Pod’ingiz `didn't match Pod's node affinity/selector` xabari bilan
   `Pending` holatda. Sababni tasdiqlaydigan ikkita buyruqni ayting.
