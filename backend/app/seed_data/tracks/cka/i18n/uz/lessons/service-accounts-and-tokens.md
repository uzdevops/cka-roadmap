## Pod’lar uchun shaxs

Foydalanuvchilar - klasterdan tashqaridagi odamlar va vositalar uchun.
**ServiceAccount** esa **Pod** qaysi shaxs sifatida ishlashini bildiradi va
klaster ichidagi dastur API bilan gaplashishi kerak bo’lganda RBAC aynan
shunga bog’lanadi - Pod’larni ro’yxatlaydigan dashboard, Job yaratadigan CI
runner, o’z CRD’larini kuzatadigan operator.

```bash
kubectl get serviceaccounts                  # har bir namespace'da `default` bor
kubectl create serviceaccount dashboard-sa
kubectl describe sa dashboard-sa
```

```yaml
spec:
  serviceAccountName: dashboard-sa           # sukut: "default"
  automountServiceAccountToken: false         # Pod API'ga murojaat qilmasa, unga token bermang
  containers: [...]
```

Har bir Pod *qandaydir* ServiceAccount sifatida ishlaydi - hech narsa
aytmasangiz, `default` sifatida. `default`’ga RBAC hech qanday ruxsat
bermagan, shuning uchun u zararsiz, lekin foydasiz ham: ruxsat kerak
bo’ladigan Pod o’z akkaunti va o’z binding’ini oladi.

```bash
kubectl create sa dashboard-sa
kubectl create role pod-reader --verb=get,list --resource=pods
kubectl create rolebinding dashboard-binding --role=pod-reader --serviceaccount=default:dashboard-sa
kubectl set serviceaccount deployment web-dashboard dashboard-sa      # Pod'larni qayta yoyadi
```

RBAC subyektlarida ServiceAccount - bu `namespace` bilan birga kelgan
`kind: ServiceAccount`; `--as`’da va xabarlarda esa u
`system:serviceaccount:<ns>:<name>` ko’rinishida bo’ladi.

## Token’lar: Pod o’zini qanday isbotlaydi

Token mount qilingan Pod ichida:

```bash
ls /var/run/secrets/kubernetes.io/serviceaccount/
# ca.crt  namespace  token
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
curl -s --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/default/pods
```

Token - API serverning `sa.key` kaliti bilan imzolangan JWT; API server uni
`sa.pub` bilan tekshiradi va ServiceAccount’ga moslaydi. 1.24 dan beri u
**bog’langan, projected va muddati tugaydigan** token: kubelet uni
TokenRequest API orqali aynan o’sha Pod uchun chiqaradi, u bir soat amal
qiladi va joyida yangilanadi, Pod yo’qolgach yaroqsiz bo’ladi. Kubelet uni
projected volume sifatida mount qiladi - `automountServiceAccountToken`
aynan shuni boshqaradi.

Pod’dan **tashqarida** turib ServiceAccount shaxsiga muhtoj har qanday narsa
uchun - CI tizimi, noutbukingizdan yuborilgan `curl` - siz token so’raysiz:

```bash
kubectl create token dashboard-sa                    # sukut bo'yicha 1 soat
kubectl create token dashboard-sa --duration=8h
TOKEN=$(kubectl create token dashboard-sa)
curl -sk https://<apiserver>:6443/api/v1/pods -H "Authorization: Bearer $TOKEN"
kubectl config set-credentials dashboard --token=$TOKEN
```

## Eski usul va uni nega hali ham ko’rishingiz mumkin

1.24 gacha har bir ServiceAccount `kubernetes.io/service-account-token`
turidagi **Secret** olardi; uning ichida muddati tugamaydigan token bo’lib,
`describe sa` chiqishida `Tokens:` ostida ko’rinardi. Yangi klasterlar bunday
Secret’larni endi yaratmaydi. Topshiriq uzoq muddatli tokenni talab qilsa,
uni hali ham qo’lda yasashingiz mumkin:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-sa-token
  annotations:
    kubernetes.io/service-account.name: dashboard-sa
type: kubernetes.io/service-account-token
```

`data.token`’ni controller manager to’ldiradi. Unga muddati hech qachon
tugamaydigan parol sifatida qarang, chunki u aynan shunday.

:::exam-tip
"ServiceAccount yarating va unga X bering" - bu uchta buyruq: `create sa`,
`create role` (yoki mavjud ClusterRole’dan foydalaning), `create rolebinding
--serviceaccount=<ns>:<name>`. "Unga token oling" - bu `kubectl create token
<name>`. Zamonaviy klasterda Secret qidirib yurmang - o’zingiz yaratmasangiz,
u yerda hech narsa yo’q.
:::

## Uni cheklab qo’yish

- API’ga hech qachon murojaat qilmaydigan workload’lar uchun - ular
  ko’pchilik - Pod spec’ida (yoki ServiceAccount’da)
  `automountServiceAccountToken: false`.
- `default`’ga hech narsa bermang; har bir workload’ga o’z akkauntini bering.
- ServiceAccount’dagi `imagePullSecrets` uni ishlatadigan har bir Pod’ga
  meros bo’lib o’tadi - registry hisob ma’lumotlari uchun qulay joy.
- Audit: subyekt sifatida `system:serviceaccounts` turgan joylarni
  `kubectl get rolebindings,clusterrolebindings -A -o json | jq` bilan
  qidiring - bunday narsa klasterdagi *har bir* Pod’ga nimadir beradi.

## O’zingizni tekshiring

1. Pod `serviceAccountName`’ni ko’rsatmagan. Uning shaxsi qanday bo’ladi va u
   nima qila oladi?
2. Klasterdan tashqarida ishlatish uchun ServiceAccount tokenini qanday
   olasiz va u qancha muddat amal qiladi?
3. `/var/run/secrets/kubernetes.io/serviceaccount/`’ga nima mount qilinadi va
   Pod’ning qaysi maydoni buni o’chiradi?
