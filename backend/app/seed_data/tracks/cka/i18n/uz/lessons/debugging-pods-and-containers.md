## Ilova nosozligi ustida old tomondan ishlash

Ikki qatlamli ilova: Service ortidagi web Pod, o’zining Service’i ortidagi
ma’lumotlar bazasi Pod’i bilan gaplashadi. "Sayt ishlamayapti."
Foydalanuvchi turgan joydan boshlang va **ichkariga** qarab yuring - har
safar bitta qadam, har bir qadamni keyingisidan oldin tekshirib.

```
 foydalanuvchi ──▶ web-service (NodePort 30081) ──▶ web Pod :8080 ──▶ db-service :3306 ──▶ db Pod :3306
```

### 1-qadam: kirish eshigi

```bash
curl -m 3 http://<node-ip>:30081                # foydalanuvchi ko'radigan narsa
kubectl get svc web-service -n shop
kubectl describe svc web-service -n shop
#   Selector: name=webapp-mysql      Port: 8080  TargetPort: 8080  NodePort: 30081
#   Endpoints: 10.244.1.5:8080       <- bu yerda BO'SH = Service hech bir Pod'ga mos kelmayapti
```

Service - bu selector va portlar. Tekshiring:

- **Endpoints bo’sh emasmi?** `kubectl get ep web-service -n shop`. Bo’sh
  bo’lsa, selector hech bir **ready** Pod’ga mos kelmayapti degani:
  label’lar farq qiladi (`name=webapp` va `name=webapp-mysql` - klassik
  holat) yoki Pod Ready emas.
- **Portlar to’g’rimi?** `port` - Service’niki; `targetPort`
  **konteynerning** tinglayotgan porti bo’lishi shart; `nodePort` -
  foydalanuvchiga aytilgani.

```bash
kubectl get pods -n shop --show-labels
kubectl get pods -n shop -l name=webapp-mysql      # selector aslida nimaga mos kelyapti
```

### 2-qadam: web Pod

```bash
kubectl get pods -n shop
kubectl describe pod webapp-mysql -n shop | tail -25
kubectl logs webapp-mysql -n shop
kubectl logs webapp-mysql -n shop --previous        # qulagan konteynerning chiqishi
```

| STATUS | Ma’nosi | Nimaga qarash kerak |
|---|---|---|
| `Pending` | rejalashtirilmagan | Events: cpu/memory yetarli emas, taint’lar, nodeSelector, PVC Pending |
| `ContainerCreating` | rejalashtirilgan, ishga tushmagan | Events: volume mount bo’lmadi, ConfigMap/Secret yo’q, image tortilyapti |
| `ImagePullBackOff` / `ErrImagePull` | image | nom/teg xatosi, imagePullSecret’siz yopiq registry, tarmoq yo’q |
| `CreateContainerConfigError` | config | murojaat qilingan ConfigMap/Secret kaliti mavjud emas |
| `CrashLoopBackOff` | ishga tushadi va o’ladi | `logs --previous`; exit code; command/args; yetishmayotgan env/config |
| `OOMKilled` (describe ichida) | memory limiti | `limits.memory`’ni oshiring yoki sizib chiqishni tuzating |
| `Error` / `Completed` | ishladi va chiqib ketdi | Job uchun normal; server uchun xato - jarayon chiqib ketgan |
| `Running`, lekin `0/1` READY | readiness probe o’tmayapti | probe path/port; ilova hali tinglamayapti |
| `Running` `1/1` va baribir buzuq | ilovaning o’zi | loglar, env, ichkariga exec qilib bog’liqlikka curl |

`describe` ichida **Last State** ostidagi exit code’lar: `1` - ilova
xatosi, `137` - o’ldirilgan (OOM yoki evict), `139` - segfault, `143` -
SIGTERM, `126/127` - buyruq topilmadi yoki bajariladigan emas (noto’g’ri
`command:`).

### 3-qadam: ilovaga nima aytilgan

```bash
kubectl describe pod webapp-mysql -n shop | grep -A8 Environment
#   DB_Host:      mysql-service
#   DB_User:      root
#   DB_Password:  <set to the key 'password' in secret 'db-secret'>
kubectl exec -it webapp-mysql -n shop -- env | grep DB_
kubectl exec -it webapp-mysql -n shop -- nslookup mysql-service
kubectl exec -it webapp-mysql -n shop -- nc -zv mysql-service 3306
```

Noto’g’ri `DB_Host` (Service `mysql-service` bo’lgani holda `mysql`),
noto’g’ri parol, noto’g’ri port - ilovaning logi "connection refused" yoki
"access denied" deydi; env esa nega shundayligini ko’rsatadi.

### 4-qadam: ma’lumotlar bazasi Service’i va Pod’i

O’sha ikki tekshiruvning o’zi, bitta qadam ichkarida:

```bash
kubectl get svc,ep mysql-service -n shop        # endpoints bo'sh emasmi? port 3306 → targetPort 3306?
kubectl get pods -n shop -l name=mysql          # Service selector'iga mos kelyaptimi?
kubectl logs mysql -n shop                      # MySQL ishga tushdimi? parol env'i o'rnatilganmi?
kubectl describe pod mysql -n shop | grep -A4 Environment
```

## Tuzatish

Ko’pchilik tuzatishlar bitta maydon: label, port, env qiymati, image teg.

```bash
kubectl edit svc web-service -n shop            # selector / portlar - Service'lar joyida tahrirlanadi
kubectl edit deployment web -n shop             # env, image, probe'lar - yangi Pod'lar chiqaradi
kubectl edit pod webapp-mysql -n shop           # faqat image/bir nechta maydon; qolgan hamma narsa uchun:
kubectl get pod webapp-mysql -n shop -o yaml > p.yaml   # tahrirlang, keyin `kubectl replace --force -f p.yaml`
```

Keyin **kirish eshigida tekshiring**: NodePort’ga yana `curl` qiling yoki
`kubectl port-forward svc/web-service 8080:8080 -n shop` qilib
localhost’ga curl qiling.

:::exam-tip
Imtihonning ilova nosozligi savollari - aynan shu yurish, ular aytgan
namespace’da. Tartib bilan tekshiring - Service endpoint’lari, selector va
label’lar, portlar, Pod statusi, loglar, env, keyingi qadam - va uni besh
daqiqadan kamroq vaqtda topasiz. Bitta ekranda
`kubectl get all -n <ns> -o wide --show-labels` - eng tez birinchi qarash.
:::

## O’zingizni tekshiring

1. Service’ning Endpoints’i bo’sh. Buning ikkita sababi qaysi va qaysi
   buyruq ularni bir-biridan ajratadi?
2. Pod `Running`, lekin `0/1` READY. Nima ishlamayapti va nima ishlayapti?
3. Web Pod’ning logi "cannot connect to mysql" deydi. Keyingi uchta
   tekshiruvni tartib bilan sanang.
