## Asosiy resurs - vaqt

Ikki soat, o’n besh-yigirmata vazifa: har biriga olti-sakkiz daqiqadan,
o’qish, kontekst almashtirish, tekshirish va noto’g’ri ketadigan o’sha
bitta vazifa bilan birga. Bitta qatorli buyruqda tejalgan har bir daqiqa -
13% turadigan nosozlik vazifasiga qoladigan daqiqa. Bu dars - siz odatda
qilayotgan usuldan tezroq bo’lgan narsalar ro’yxati.

## Nolinchi daqiqa: terminal

```bash
alias k=kubectl                                  # odatda imtihonda oldindan qo'yilgan; tekshiring
export do="--dry-run=client -o yaml"             # k run x --image=nginx $do > x.yaml
export now="--force --grace-period=0"            # k delete pod x $now
source <(kubectl completion bash); complete -o default -F __start_kubectl k
```

```bash
printf 'set ts=2 sw=2 et ai nu\n' >> ~/.vimrc
```

(`et` tab’larni bo’sh joyga aylantiradi - YAML’dagi tab sintaksis xatosi;
`ai` avtomatik chekinish; `nu` xato xabarlari uchun qator raqamlari.)
vim’da: hujjatlardan nusxa ko’chirishdan oldin `:set paste`, chekinishni
oshirish/kamaytirish uchun visual blok bilan `>>`/`<<`, `u` - undo.

## Generatorlar

Imperativ `create`/`run` ga ega har bir obyekt va muhim bo’lgan flag’lar:

| Obyekt | Buyruq |
|---|---|
| Pod | `k run web --image=nginx --port=80 -l app=web --env=A=1 --command -- sleep 3600` |
| Pod, bir martalik | `k run tmp --image=busybox:1.28 --rm -it --restart=Never -- sh` |
| Deployment | `k create deploy web --image=nginx --replicas=3 --port=80` |
| Deployment/Pod’dan Service | `k expose deploy web --name=web-svc --port=80 --target-port=8080 --type=NodePort` |
| Mustaqil Service | `k create svc clusterip web --tcp=80:8080`; `k create svc nodeport web --tcp=80:8080 --node-port=30080` |
| Job | `k create job j --image=busybox -- sh -c "echo hi"` |
| CronJob | `k create cj cj --image=busybox --schedule="*/5 * * * *" -- sh -c "date"` |
| ConfigMap | `k create cm c --from-literal=K=V --from-file=app.conf --from-env-file=.env` |
| Secret | `k create secret generic s --from-literal=pass=x`; `... tls t --cert= --key=`; `... docker-registry r --docker-server= ...` |
| Namespace / SA | `k create ns x`; `k create sa x` |
| Role / ClusterRole | `k create role r --verb=get,list --resource=pods,pods/log`; `k create clusterrole cr --verb=get --resource=nodes` |
| RoleBinding / CRB | `k create rolebinding rb --role=r --user=u --serviceaccount=ns:sa`; `k create clusterrolebinding crb --clusterrole=cr --group=g` |
| Ingress | `k create ingress i --rule="host/path=svc:80" --class=nginx --annotation k=v` |
| Quota / limitlar | `k create quota q --hard=pods=10,cpu=4`; (LimitRange: YAML) |
| PriorityClass | `k create priorityclass high --value=1000` |
| Token | `k create token <sa>` |
| HPA | `k autoscale deploy web --min=2 --max=5 --cpu-percent=50` |
| Taint / label / annotate | `k taint node n k=v:NoSchedule`; `k label node n disk=ssd`; `k annotate deploy d kubernetes.io/change-cause="..."` |
| Scale / image / rollout | `k scale deploy web --replicas=5`; `k set image deploy web nginx=nginx:1.27`; `k rollout undo/status/history deploy web` |
| Node amallari | `k cordon n`; `k drain n --ignore-daemonsets --delete-emptydir-data`; `k uncordon n` |

Bularga generator yo’q: PV, PVC, StorageClass, NetworkPolicy, DaemonSet,
StatefulSet, LimitRange, static Pod’larni joylashtirish, asosiylardan
tashqaridagi Pod maydonlari. Ular uchun: **eng yaqinini generatsiya
qiling, keyin tahrirlang** (`k run ...
$do > f.yaml`; `k create deploy ... $do` va `kind`ni o’zgartiring) yoki
hujjatlardan ko’chiring.

## dry-run shablonlari

```bash
k run web --image=nginx $do > web.yaml; vi web.yaml; k apply -f web.yaml        # generatsiya qiling, maydon qo'shing, apply qiling
k create deploy web --image=nginx $do | sed 's/kind: Deployment/kind: DaemonSet/' > ds.yaml   # turini almashtirish
k get deploy web -o yaml > web.yaml                                              # jonli obyektni tahrirlash uchun eksport qilish
k apply -f x.yaml --dry-run=server                                               # yaratmasdan API bo'yicha tekshirish
k run web --image=nginx $do | k apply -f -                                       # $do'siz variant bilan bir xil, lekin birikadi
```

## Jonli obyektni tahrirlash

| Obyekt | Joyida bo’ladimi? |
|---|---|
| Deployment, Service, ConfigMap, Role, NetworkPolicy, PV... | `k edit` - ha |
| Pod | faqat image, activeDeadlineSeconds, tolerations (qo’shish). Aks holda: `k edit` → rad etiladi → `k replace --force -f /tmp/kubectl-edit-*.yaml` |
| Static Pod | `/etc/kubernetes/manifests` ichidagi faylni tahrirlang |
| O’zgarmas maydon | `k delete` + `k apply`, yoki `k replace --force` |

```bash
k edit pod web              # tez qarab, tez tuzatish
k patch deploy web -p '{"spec":{"replicas":4}}'
k set env deploy web MODE=prod
k set resources deploy web -c nginx --limits=memory=256Mi
k set serviceaccount deploy web sa-name
```

## Hujjatlardan tezroq qidirish

```bash
k explain pod.spec.tolerations             # har bir maydon, turi va tavsifi bilan
k explain deploy.spec.strategy --recursive
k create role --help | grep -A5 Examples   # har bir `create` da Examples bor
k api-resources | grep -i netpol           # qisqa nomlar va namespace'ga tegishlimi
k api-resources --namespaced=false
```

## Tez tekshirish

```bash
k get all -n ns -o wide --show-labels       # bitta ekran
k get pod x -o jsonpath='{.spec.containers[*].image}'
k get pod x -w                              # Running bo'lguncha kuzating, Ctrl-C
k describe pod x | tail -15                 # faqat Events
k logs x --tail=20
k rollout status deploy x
k auth can-i get pods --as user -n ns
```

## Mashqlar

Har birini vaqt bilan bajaring, maqsad qavs ichida. Maqsadni ketma-ket uch
marta ura olmaguningizcha takrorlang.

1. Yangi `drill` namespace’ida `app=d1` label’li `drill1` nomli
   nginx:alpine Pod’i, 80-portda ClusterIP sifatida ochilgan, keyin
   NodePort 30085. **[90 s]**
2. `drill2` Deployment’i, 3 replika nginx:1.25 → image’ni 1.26 ga qo’ying →
   rollout’ni tekshiring → undo → change-cause annotatsiyasini yozing.
   **[90 s]**
3. `pod-reader` Role’i (pods uchun get, list, watch) + `drill/reader`
   ServiceAccount’i uchun RoleBinding, keyin uning nomidan `auth can-i`.
   **[60 s]**
4. Control plane’da `sleep 1d` bilan busybox `drill4` static Pod’i.
   **[60 s]**
5. `$do` + vi orqali `/cache` da emptyDir va `requests.cpu: 100m` bilan
   `drill5` Pod’i. **[90 s]**
6. `drill` ichida default-deny ingress NetworkPolicy, keyin `role=fe` dan
   `app=d1` ga 80-portni ochish. **[120 s]**
7. Har bir node’ning nomi va InternalIP’sini faylga eksport qiling.
   **[45 s]**
8. `/opt/s.db` ga etcd snapshot va `snapshot status`. **[90 s]**
9. Worker’ni `cordon`, `drain`, `uncordon` qiling; Pod’lar ko’chganini
   tasdiqlang. **[60 s]**
10. Buzilgan image tag’li Deployment’ni toping (bittasini yarating), uni
    `set image` bilan tuzating, Available bo’lganini tasdiqlang. **[60 s]**

:::exam-tip
Eng qimmatli yagona odat: **hech qachon YAML’ni bo’sh fayldan yozmang**.
`k run`/`k create ... $do`, `k get ... -o yaml` yoki hujjatlar - keyin uch
qatorni tahrirlang. Bo’sh fayldan YAML yozish sekin va bosim ostida
ko’rmaydigan chekinish xatolarini keltirib chiqaradi.
:::

## O’zingizni tekshiring

1. Qaysi obyektlarda imperativ generator yo’q va ularning o’rniga nima
   qilasiz?
2. Ishlab turgan Pod’dagi o’zgarmas maydonni o’zgartirishning eng tez yo’li
   qaysi?
3. `web` nomli Deployment uchun 80-portda, nodePort `30080` bilan NodePort
   Service yaratadigan bitta buyruqni yozing.
