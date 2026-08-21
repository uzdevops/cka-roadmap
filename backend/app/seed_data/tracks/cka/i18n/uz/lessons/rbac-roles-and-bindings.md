## Role nimani aytadi; binding kimni aytadi

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: dev
rules:
  - apiGroups: [""]                      # core guruh: pods, services, configmaps...
    resources: ["pods"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["pods/log"]               # subresurs - o'zi alohida resurs
    verbs: ["get"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["app-config"]         # ixtiyoriy: faqat shu bitta obyekt
    verbs: ["get", "update"]
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: dev
subjects:
  - kind: User
    name: dev-user                        # sertifikatidagi CN yoki OIDC foydalanuvchi nomi
    apiGroup: rbac.authorization.k8s.io
  - kind: Group
    name: developers                      # sertifikatidagi O
    apiGroup: rbac.authorization.k8s.io
  - kind: ServiceAccount
    name: builder
    namespace: dev                        # ServiceAccount'da apiGroup emas, namespace bo'ladi
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

Binding’da **bitta** roleRef va **ko’plab** subyekt bo’ladi. `roleRef`
o’zgarmas - binding’ni boshqa Role’ga yo’naltirmoqchi bo’lsangiz, uni
o’chirib qaytadan yaratasiz.

## Imperativ yo’l, ya’ni imtihon yo’li

```bash
kubectl create role developer -n dev \
  --verb=get,list,watch,create,delete --resource=pods \
  --verb=get --resource=pods/log
kubectl create role developer -n dev --verb=get,list --resource=deployments.apps      # noaniq bo'lsa nuqtadan keyin guruh

kubectl create rolebinding developer-binding -n dev --role=developer --user=dev-user
kubectl create rolebinding developer-binding -n dev --role=developer --group=developers
kubectl create rolebinding builder-binding -n dev --role=developer --serviceaccount=dev:builder

kubectl get roles,rolebindings -n dev
kubectl describe role developer -n dev            # qoidalarning o'qish oson jadvali
kubectl describe rolebinding developer-binding -n dev
kubectl auth can-i create pods --as dev-user -n dev      # yes
kubectl auth can-i create pods --as dev-user              # no - noto'g'ri namespace
```

`kubectl create role` bir nechta `--verb`/`--resource` juftligini qabul
qiladi; har bir `--resource`’dan oldin turgan verb’lar o’shanga tegishli
bo’ladi. Shubhalansangiz, `$do` bilan yarating va u chiqargan YAML’ni o’qing.

:::exam-tip
Har qanday RBAC topshirig’ini tugatishdan oldin uchta tekshiruv: Role’da ham,
RoleBinding’da ham **namespace** (`default`’dagi Role `dev` uchun hech narsa
qilmaydi); **apiGroups** (`""` yoki `apps`); va `kubectl auth can-i <verb> <resource>
--as <user> -n <ns>` buyrug’i `yes` qaytarishi. Agar topshiriqda "va
foydalanuvchi kubectl logs ishlata olishi kerak" ham deyilgan bo’lsa,
`pods/log` qo’shing.
:::

## Namespace ichida ClusterRole’ni bog’lash

RoleBinding Role o’rniga **ClusterRole**ga murojaat qila oladi. Ruxsatlar
baribir binding turgan namespace bilan chegaralanadi - "viewer nima qila
oladi" degan to’plamni bir marta ClusterRole sifatida aniqlab, keyin uni har
bir namespace’ga tarqatish aynan shu tarzda bo’ladi:

```bash
kubectl create rolebinding ana-view -n dev --clusterrole=view --user=ana
```

O’rnatilgan `view`, `edit`, `admin` (namespace admini) va `cluster-admin`
ClusterRole’lari aynan shuning uchun; `kubectl describe clusterrole edit`
oqilona "developer" to’plami qanday ko’rinishini ko’rsatadi.

## Kimdir nima qila olishini o’qish

```bash
kubectl auth can-i --list --as dev-user -n dev
kubectl get rolebindings -n dev -o wide                       # SUBJECTS ustuni
kubectl get rolebindings -A -o json | jq -r '.items[] | select(.subjects[]?.name=="dev-user") | "\(.metadata.namespace)/\(.metadata.name)"'
```

`kubectl get permissions-for user` degan narsa yo’q; oxirgi qator - halol
yo’l, `can-i --list` esa tez yo’l.

## Sokin "Forbidden" chiqaradigan xatolar

| Xato | Alomat |
|---|---|
| Pod’lar uchun `apiGroups: ["apps"]` | `pods is forbidden ... in API group ""` |
| `resources: ["pod"]` (birlikda) yoki `["Pods"]` | forbidden; resurs nomlari ko’plikda va kichik harfda |
| Role noto’g’ri namespace’da | siz nazarda tutgan namespace’da forbidden |
| `verbs: ["get"]`, lekin foydalanuvchi `kubectl get pods` ishlatadi | forbidden: bu `list` |
| subyekt `kind: User` va `name: dev-user`, lekin sertifikat CN’i `developer` | forbidden: nom aynan mos kelishi kerak |
| `namespace:`’siz ServiceAccount subyekti | binding yaratiladi, lekin hech nimaga mos kelmaydi |

## O’zingizni tekshiring

1. `dev` namespace’da Pod’lar ustidan get/list/watch va ularning loglari
   ustidan get beradigan Role’ni, hamda `dev-user` foydalanuvchisi uchun
   RoleBinding’ni yozing - ikkita `kubectl create` buyrug’i ko’rinishida.
2. RoleBinding bilan Role’ni bog’lash va ClusterRole’ni bog’lash orasida
   qanday farq bor?
3. `kubectl auth can-i get pods --as dev-user -n dev` yes deydi, lekin
   dev-user sifatida `kubectl get pods -n dev` Forbidden deydi. Qaysi verb
   yetishmayapti?
