## RBAC qaysi lug’atda yoziladi

Har bir RBAC qoidasi "shu **API guruh**dagi shu **resurslar** ustidan shu
**verb**lar" deydi. Resurs qaysi guruhda ekanini bilmasangiz, qoidani yoza
olmaysiz - `apiGroups: [""]` va `apiGroups: ["apps"]` orasidagi farq esa
ishlaydigan Role bilan indamay hech narsa bermaydigan Role orasidagi farqdir.

```bash
curl -sk https://localhost:6443/ --cert admin.crt --key admin.key --cacert ca.crt
kubectl get --raw / | jq .paths        # o'shaning o'zi, kubectl hisob ma'lumotlari orqali
# "/api", "/apis", "/healthz", "/metrics", "/openapi/v2", "/version", ...
```

Ikkita ildiz muhim:

| Yo’l | Nomi | Nimani saqlaydi |
|---|---|---|
| `/api` | **core** (eski) guruh | Pod’lar, Service’lar, Namespace’lar, Node’lar, ConfigMap’lar, Secret’lar, PV’lar, PVC’lar, ServiceAccount’lar, Event’lar, Endpoint’lar |
| `/apis` | **nomlangan** guruhlar | qolgan hamma narsa |

```
/api/v1/namespaces/default/pods
/apis/apps/v1/namespaces/default/deployments
/apis/batch/v1/namespaces/default/jobs
/apis/networking.k8s.io/v1/namespaces/default/ingresses
/apis/rbac.authorization.k8s.io/v1/clusterroles
/apis/storage.k8s.io/v1/storageclasses
/apis/certificates.k8s.io/v1/certificatesigningrequests
```

URL’ning o’zi *tuzilma*: `/apis/<group>/<version>/namespaces/<ns>/<resource>/<name>`,
core guruhda esa `<group>` bo’lagi yo’q - shuning uchun uning RBAC’dagi
apiGroup’i bo’sh satrdir.

## Yodda turadigan jadval

| Guruh | RBAC `apiGroups` da | Resurslar |
|---|---|---|
| core | `""` | pods, services, configmaps, secrets, namespaces, nodes, persistentvolumes, persistentvolumeclaims, serviceaccounts, events, endpoints |
| `apps` | `apps` | deployments, replicasets, daemonsets, statefulsets |
| `batch` | `batch` | jobs, cronjobs |
| `networking.k8s.io` | `networking.k8s.io` | ingresses, networkpolicies, ingressclasses |
| `rbac.authorization.k8s.io` | `rbac.authorization.k8s.io` | roles, rolebindings, clusterroles, clusterrolebindings |
| `storage.k8s.io` | `storage.k8s.io` | storageclasses, volumeattachments |
| `certificates.k8s.io` | `certificates.k8s.io` | certificatesigningrequests |
| `autoscaling` | `autoscaling` | horizontalpodautoscalers |
| `policy` | `policy` | poddisruptionbudgets |
| `apiextensions.k8s.io` | `apiextensions.k8s.io` | customresourcedefinitions |

```bash
kubectl api-resources                       # har bir resurs, guruhi, qisqa nomi, namespace'limi?, kind
kubectl api-resources --namespaced=false    # faqat klaster darajasidagilar
kubectl api-resources --api-group=apps
kubectl api-versions                        # server beradigan har bir guruh/versiya
```

`kubectl api-resources` - bu jadvalning *sizning* klasteringiz uchun ishonchli
varianti, CRD’lar bilan birga. Uning APIVERSION ustuni - aynan manifestdagi
`apiVersion` ga yoziladigan satr, uning guruh qismi esa RBAC’ga tushadigan
narsa.

## Resurslar, subresurslar, verb’lar

**Resurs** - bu ot (`pods`); **subresurs** - uning o’z yo’li orqali
kiriladigan bir tomoni: `pods/log`, `pods/exec`, `pods/status`,
`deployments/scale`. RBAC ularni `resources: ["pods/log"]` ko’rinishida
nomlaydi - `pods` ustidan `get` berish `pods/log` ustidan `get` **bermaydi**;
`kubectl logs` uchun subresurs kerak.

**Verb’lar** - bu Kubernetes nomlariga ega HTTP metodlari:

| Verb | HTTP | kubectl |
|---|---|---|
| `get` | bitta obyektga GET | `get pod x`, `describe` |
| `list` | to’plamga GET | `get pods` |
| `watch` | watch bilan GET | `get pods -w`, har bir kontroller |
| `create` | POST | `create`, `run`, `apply` (yangi) |
| `update` | PUT | `replace`, `edit` |
| `patch` | PATCH | `patch`, `apply` (mavjud), `set image`, `scale` |
| `delete` | DELETE | `delete` |
| `deletecollection` | to’plamga DELETE | `delete pods --all` |

:::exam-tip
Role "ishlamayapti" deyilganda uchta narsani shu tartibda tekshiring:
`apiGroups` (Pod va Service uchun `""`, Deployment uchun `apps`), resursning
**ko’plikdagi kichik harfli** nomi (`Deployment` emas, `deployments`) va
foydalanuvchiga aslida kerak bo’lgan verb `get` emas, `list` emasmi (`get pods`
uchun). `kubectl
auth can-i list pods --as dev-user -n dev` buni bitta satrda aytib beradi.
:::

## API bilan bevosita gaplashish

```bash
kubectl proxy &                          # localhost:8001, sizning kubeconfig hisob ma'lumotlaringiz bilan
curl localhost:8001/apis/apps/v1/namespaces/default/deployments | jq '.items[].metadata.name'
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes | jq .
```

`kubectl proxy` - bu `kube-proxy` emas: biri - siz uchun API serverga
qaratilgan lokal HTTP proxy; ikkinchisi - har bir node’dagi Service
marshrutlagichi. So’z bir xil, vazifalari esa bir-biriga aloqasiz.

## O’zingizni tekshiring

1. Pod’lar uchun va Deployment’lar uchun `apiGroups` qiymati qanday?
2. Role `pods` ustidan `get` va `list` beradi, lekin `kubectl logs` hamon
   taqiqlangan. Nega?
3. Qaysi buyruq sizning klasteringizdagi har bir resursni API guruhi bilan
   sanab beradi?
