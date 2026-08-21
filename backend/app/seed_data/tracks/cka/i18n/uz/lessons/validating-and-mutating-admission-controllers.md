## O’zingiz yozadigan admission

O’rnatilgan pluginlar keng tarqalgan siyosatlarni qoplaydi. Qolgan hamma narsa
uchun - "bu namespace’dagi har bir Pod `team` label’iga ega bo’lishi shart",
"hamma joyga bizning logging sidecar’imizni kiriting", "biz ishonmaydigan
registry’lardan kelgan image’larni rad eting" - API server **sizning** HTTP
xizmatingizni chaqirib, qarorni unga qoldira oladi. Chaqiruvni ikkita
o’rnatilgan plugin bajaradi:

- **MutatingAdmissionWebhook** - xizmatingiz obyektga qo’llanadigan JSON patch
  qaytarishi mumkin.
- **ValidatingAdmissionWebhook** - xizmatingiz xabar bilan birga ruxsat
  berildi yoki rad etildi deb qaytaradi.

Avval mutating webhook’lar ishlaydi (shunda validating’lar yakuniy obyektni
ko’radi), keyin sxema validatsiyasi, so’ng validating webhook’lar. Bir nechta
mutating webhook ketma-ket ishlaydi; validating webhook’lar esa parallel
ishlaydi va ulardan istalgan biri rad eta oladi.

```
obyekt ─▶ [mutating webhook A] ─▶ [mutating webhook B] ─▶ sxemani tekshirish ─▶ [validating webhook'lar...] ─▶ etcd
```

## Uchta qism

1. **Webhook server** - `AdmissionReview` so’rovini qabul qilib,
   `AdmissionReview` javobi bilan javob beradigan istalgan HTTPS xizmat.
   Odatda klaster ichida Deployment va Service sifatida ishlaydi; API server
   ishonadigan sertifikat bilan TLS xizmatini berishi shart.
2. **Konfiguratsiya obyekti** - API serverga uni qachon va qayerda chaqirishni
   aytadi:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy.example.com
webhooks:
  - name: pod-policy.example.com
    clientConfig:
      service:
        namespace: webhook-demo
        name: webhook-server
        path: /validate
      caBundle: <base64 CA that signed the server cert>
    rules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["pods"]
    admissionReviewVersions: ["v1"]
    sideEffects: None
    failurePolicy: Fail              # yoki Ignore
    timeoutSeconds: 5
    namespaceSelector: {}            # ixtiyoriy: ba'zi namespace'lar bilan cheklash
```

   `MutatingWebhookConfiguration` ham xuddi shu shaklda.

3. Serveringiz yuboradigan **javob**:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "<same uid as the request>",
    "allowed": false,
    "status": {"message": "pods must set runAsNonRoot"}
  }
}
```

   Mutating javob bunga `"patchType": "JSONPatch"` ni va `"patch"` ichida
   base64 bilan kodlangan JSON patch’ni qo’shadi.

## failurePolicy - eng xavfli maydon

`Fail` (sukut qiymat) shuni bildiradi: agar webhook’ga yetib bo’lmasa, u
timeout bo’lsa yoki tushunarsiz javob qaytarsa, so’rov **rad etiladi**.
Xavfsizlik siyosati uchun bu to’g’ri, lekin webhook o’zining Pod’larini rad
etgani uchun ular ishga tusha olmay qolganda bu halokatli. `Ignore` esa: agar
unga yetib bo’lmasa, so’rovni o’tkazib yuboradi.

:::warning
Klasterda "endi hech narsa yaratib bo’lmayapti" holati bo’lsa va har bir
xatoda `failed calling webhook` tilga olinsa, demak `failurePolicy: Fail`
bilan ishlaydigan webhook’ning xizmati o’chgan. Tiklash yo’li -
`*WebhookConfiguration` obyektini o’chirish yoki tahrirlash: u webhook
tekshiradigan resurs emas, shuning uchun bu hali ham ishlaydi - keyin
xizmatni tuzatib, konfiguratsiyani qayta yarating.
:::

```bash
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations
kubectl describe validatingwebhookconfiguration pod-policy.example.com
kubectl delete validatingwebhookconfiguration pod-policy.example.com   # favqulodda chiqish
```

## Uning ishlashini ko’rish

```bash
kubectl run demo --image=nginx
# Error from server: admission webhook "pod-policy.example.com" denied the request: pods must set runAsNonRoot

# o'rniga securityContext kirituvchi mutating webhook bilan:
kubectl run demo --image=nginx
kubectl get pod demo -o jsonpath='{.spec.securityContext}'
# {"runAsNonRoot":true,"runAsUser":1234}   <- buni siz hech qachon yozmagansiz
```

:::exam-tip
Imtihon sizdan webhook server yozishni so’ramaydi. U berilgan manifestlardan
(Deployment, Service, caBundle’li konfiguratsiya obyekti) webhook’ni
**ro’yxatdan o’tkazishni**, so’rov nega rad etilganini tushuntirishni yoki
"failed calling webhook" ni aniqlashni so’rashi mumkin. Uchta qismni va
`failurePolicy` tuzog’ini bilsangiz, shuning o’zi yetadi.
:::

## O’rnatilgan muqobil: ValidatingAdmissionPolicy

Kubernetes 1.30 dan boshlab oddiy validatsiyani **serversiz**,
`ValidatingAdmissionPolicy` obyektidagi CEL ifodalari sifatida yozish mumkin:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-team-label
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "has(object.metadata.labels) && 'team' in object.metadata.labels"
      message: "every Deployment needs a team label"
```

va uni yoqish uchun `ValidatingAdmissionPolicyBinding`. TLS yo’q, Pod yo’q,
failurePolicy muammosi yo’q - oddiy qoidalar uchun bu yaxshiroq vosita.

## O’zingizni tekshiring

1. Mutating webhook’lar, sxema validatsiyasi va validating webhook’lar qanday
   tartibda ishlaydi va nega aynan shu tartibda?
2. Klasterda hech narsa yaratib bo’lmayapti va har bir xato `failed calling
   webhook` deyapti. Nima sodir bo’ldi va uni qanday tiklaysiz?
3. Webhook serveringizga ishonishi uchun API serverga `clientConfig` ichida
   nima kerak va u noto’g’ri bo’lsa nima bo’ladi?
