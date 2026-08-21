## kubectl chiqishi ustida JSONPath

`kubectl get <thing> -o json` - bu hujjat; `-o jsonpath='{...}'` esa so’rov.
Sof tildan ikkita farqi bor: `$` ixtiyoriy (kubectl uni o’zi qo’shadi) va
so’rov `{ }` ichiga o’raladi.

```bash
kubectl get pod web -o json | less                          # avval hujjatning o'ziga qarang
kubectl get pod web -o jsonpath='{.metadata.name}'
kubectl get pod web -o jsonpath='{.spec.containers[0].image}'
kubectl get pod web -o jsonpath='{.status.podIP}'
```

## Obyektlar ro’yxati: .items

Nomsiz ishlatilgan `kubectl get pods` obyektlari `.items` ostida turadigan
**List** qaytaradi. Deyarli har bir foydali so’rov o’sha yerdan boshlanadi.

```bash
kubectl get nodes -o jsonpath='{.items[*].metadata.name}'
# controlplane node01 node02
kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}'
kubectl get nodes -o jsonpath='{.items[*].status.capacity.cpu}'
# 4 4 4
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}'      # klasterdagi har bir image
kubectl get pv -o jsonpath='{.items[*].spec.capacity.storage}'
```

`[*]` chiqishi bitta qatorda, probel bilan ajratilgan holda keladi. Yangi
qator qo’shish uchun `{"\n"}` ishlating - literal satrlar jingalak qavs
ichida qo’sh tirnoqqa olinadi:

```bash
kubectl get nodes -o jsonpath='{.items[*].metadata.name}{"\n"}'
kubectl get nodes -o jsonpath='{.items[*].metadata.name}{"\n"}{.items[*].status.capacity.cpu}{"\n"}'
# controlplane node01 node02
# 4 4 4
```

## range: har bir element uchun bitta qator

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.cpu}{"\n"}{end}'
# controlplane    4
# node01          4
# node02          4
```

`{range list}...{end}` sikl hosil qiladi; uning ichida yo’llar joriy
elementga nisbatan yoziladi. Jadvalni qo’lda ana shunday qurasiz - va Pod →
node ro’yxatini, har bir Pod’dagi image’larni va shu kabilarni ham shunday
olasiz:

```bash
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{" → "}{.spec.nodeName}{"\n"}{end}'
```

## custom-columns: xuddi shu narsa, formatlangan holda

```bash
kubectl get nodes -o custom-columns=NODE:.metadata.name,CPU:.status.capacity.cpu,ARCH:.status.nodeInfo.architecture
# NODE           CPU   ARCH
# controlplane   4     amd64
# node01         4     amd64
kubectl get pods -o custom-columns=POD:.metadata.name,IMAGE:.spec.containers[*].image,NODE:.spec.nodeName
kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage --no-headers
```

`custom-columns=HEADER:path,HEADER:path` - jingalak qavslar yo’q, `.items`
yo’q (u siz uchun o’zi aylanib chiqadi), sarlavhalarni o’zingiz tanlaysiz.
Uni `--sort-by` bilan birga ishlating.

## --sort-by

```bash
kubectl get pv --sort-by=.spec.capacity.storage
kubectl get pv --sort-by=.spec.capacity.storage -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get nodes --sort-by=.status.capacity.cpu
kubectl get events --sort-by=.lastTimestamp
```

`--sort-by` JSONPath qabul qiladi (jingalak qavslarsiz va `.items`
ishlatmasdan) va odatdagi jadval chiqishini shu bo’yicha saralaydi.

## Filtrlar

```bash
kubectl get pods -o jsonpath='{.items[?(@.spec.nodeName=="node01")].metadata.name}'
kubectl get nodes -o jsonpath='{.items[?(@.metadata.name=="node01")].status.addresses[?(@.type=="InternalIP")].address}'
kubectl config view --kubeconfig=my-kube-config -o jsonpath='{.contexts[?(@.context.user=="aws-user")].name}'
kubectl get nodes -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}'
```

Aynan filtrlarda tirnoqlar masalasi nozik bo’ladi: shell uchun butun ifoda
atrofida bitta tirnoq, ichidagi satrlar uchun qo’sh tirnoq. Ularni
bo’lak-bo’lak qilib quring va har birini sinab ko’ring.

## JSONPath qayerda tugab, jq qayerdan boshlanadi

kubectl’ning JSONPath’ida `..` rekursiv tushish ham, arifmetika ham, satr
funksiyalari ham yo’q. Oddiy ajratib olishdan nariga o’tadigan har qanday
ish uchun `-o json | jq`:

```bash
kubectl get pods -A -o json | jq -r '.items[] | select(.status.phase!="Running") | .metadata.namespace + "/" + .metadata.name'
kubectl get nodes -o json | jq '.items[].status.allocatable'
```

jq odatda imtihon node’ida bo’ladi; `-o jsonpath` esa har doim bor.

## Imtihonning sevimli topshiriqlari

| Topshiriq | Buyruq |
|---|---|
| node nomlarini faylga | `kubectl get nodes -o jsonpath='{.items[*].metadata.name}' > /opt/nodes.txt` |
| node’larning OS image’lari | `kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}'` |
| node’ning InternalIP’si | `kubectl get node node01 -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}'` |
| sig’imi bo’yicha saralangan PV’lar, nom+hajm ustunlari bilan | `kubectl get pv --sort-by=.spec.capacity.storage -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage` |
| berilgan kubeconfig’dagi foydalanuvchining konteksti | `kubectl config view --kubeconfig=<f> -o jsonpath='{.contexts[?(@.context.user=="<u>")].name}'` |
| namespace’dagi barcha Pod’larning image’lari | `kubectl get pods -n <ns> -o jsonpath='{.items[*].spec.containers[*].image}'` |
| har bir node’dagi Pod’lar | `kubectl get pods -A -o custom-columns=POD:.metadata.name,NODE:.spec.nodeName --sort-by=.spec.nodeName` |

:::exam-tip
Topshiriqda "chiqishni /opt/file ga yozing" deyilgan bo’lsa, `jsonpath`
chiqishini `>` bilan yo’naltiring; `cat` bilan tekshiring - yetishmayotgan
`{"\n"}` muammo emas, ortiqcha `[ ]` yoki bo’lmasligi kerak bo’lgan sarlavha
esa muammo. "saralangan" uchun `--sort-by`; "ustunlar" uchun
`custom-columns`; "qiymati" uchun `-o jsonpath`. Yo’ldan ishonchingiz komil
bo’lmasa, har doim avval `kubectl get ... -o json | less` qiling - maydon
nomlarini taxmin qilish o’n soniya qarab olishdan qimmatroqqa tushadi.
:::

## O’zingizni tekshiring

1. Har bir node’ning nomi va uning InternalIP’sini har birini alohida
   qatorda chiqaradigan buyruqni yozing.
2. `--sort-by` nimani qabul qiladi va uning jq’dagi saralashdan farqi nima?
3. PV nomlari va sig’imlarini sig’im bo’yicha saralab ro’yxatlaydigan
   buyruqni yozing.
