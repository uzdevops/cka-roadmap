## O’ylab o’tirmasdan bajariladigan ikkita checklist

Oldingi darslar **nega** ekanini tushuntirdi. Bu dars esa **nima qilish**
haqida: "ulana olmayapti" va "mount bo’lmayapti" uchun ikkita tartiblangan
checklist - biror qator javobning o’zi bo’lguncha yuqoridan pastga qarab
bajaring.

## Checklist A - ulanish

Simptom: biror narsa boshqa narsaga yeta olmayapti. Ikkala uchni va yo’lni
nomlang, keyin har bir hop’ni tekshiring.

```
 client Pod ──(DNS)──▶ Service name ──▶ ClusterIP ──(kube-proxy)──▶ Endpoints ──(CNI)──▶ server Pod:port ──▶ process listening
```

| # | Tekshiruv | Buyruq | Ishlamasa |
|---|---|---|---|
| 1 | server Pod Running va **Ready** | `kubectl get pod <p> -n <ns>` | ilova qatlami (status, probe’lar, loglar) |
| 2 | jarayon portni **tinglayaptimi** | `kubectl exec <p> -- ss -lntp` yoki `netstat -lntp`, yoki ichkaridan `curl localhost:<port>` | noto’g’ri `containerPort`/ilova konfiguratsiyasi; ilova `0.0.0.0` o’rniga `127.0.0.1` ga bog’lanadi |
| 3 | Pod IP’siga boshqa Pod’dan yetib bo’ladimi | `kubectl exec <client> -- curl -m3 <pod-ip>:<port>` | CNI yoki **NetworkPolicy** (`kubectl get netpol -n <ns>`; `describe`) |
| 4 | Service’da **Endpoints** bormi | `kubectl get ep <svc> -n <ns>` | selector ≠ Pod label’lari, yoki Pod’lar Ready emas, yoki noto’g’ri namespace |
| 5 | Service portlari mos kelyaptimi | `kubectl describe svc <svc>`: `Port` → `TargetPort` = konteynerning porti; nomlangan port mavjud | `targetPort` ni tuzating (raqam yoki konteyner portining **nomi**) |
| 6 | ClusterIP’ga yetib bo’ladimi | Pod ichidan `curl -m3 <cluster-ip>:<port>` | kube-proxy (DaemonSet sog’lommi? config yo’li to’g’rimi?) |
| 7 | nom resolve bo’lyaptimi | `nslookup <svc>.<ns>.svc.cluster.local` | CoreDNS, `kube-dns` endpoint’lari, Pod’ning `resolv.conf` fayli, udp/53 ustidagi NetworkPolicy |
| 8 | namespace’lararo nom | faqat `<svc>` emas, `<svc>.<ns>` ishlatilyaptimi | DNS search domenlari faqat Pod’ning o’z namespace’ini qamraydi |
| 9 | tashqaridan NodePort | `curl <node-ip>:<nodePort>`; `kubectl get svc` da TYPE NodePort | node’dagi firewall; noto’g’ri node IP’si; Service turi ClusterIP |
| 10 | Ingress | `kubectl describe ingress`; kontroller Pod’ining loglari; backend Service **nomi va porti** mos; IngressClass o’rnatilgan; host header | Ingress mavjud bo’lmagan Service/portga ishora qiladi; kontroller yo’q; `ingressClassName` yo’q |
| 11 | NetworkPolicy | `kubectl get netpol -A`; ulardan biri server yoki client Pod’ini **tanlaydimi**? | allow’siz default-deny; client’da `policyTypes` ichida Egress bor; port/protokol mos emas; DNS egress qoidasi yo’q |

Foydali bir martalik client’lar:

```bash
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -n <ns> -- sh      # wget, nslookup, nc
kubectl run tmp --rm -it --image=nicolaka/netshoot --restart=Never -- bash        # curl, dig, ss, tcpdump
kubectl debug -it <pod> --image=busybox:1.36 --target=<container>                # distroless Pod'ning namespace'iga kirish
```

## Checklist B - storage

Simptom: Pod `Pending` yoki `ContainerCreating`, yoki ilova yoza olmayotganini
aytadi.

```
 Pod volumes: ──▶ PVC ──(bound?)──▶ PV ──(on this node? provisioner?)──▶ mount ──▶ permissions in the container
```

| # | Tekshiruv | Buyruq | Ishlamasa |
|---|---|---|---|
| 1 | Pod Events | `kubectl describe pod <p>` → `FailedScheduling`, `FailedMount`, `FailedAttachVolume` | xabarning o’zi volume’ni ham, sababni ham nomlaydi |
| 2 | PVC **Bound**mi? | `kubectl get pvc -n <ns>` | `Pending`: mos PV yo’q yoki provisioner yo’q - keyingi qatorlarga qarang |
| 3 | PVC ↔ PV mosligi | `kubectl describe pvc`: so’ralgan **hajm ≤** PV hajmi, bir xil **accessModes**, bir xil **storageClassName** (bo’sh va nomlangan - bu moslik emas), selector label’lari | farq qilgan tomonini tuzating, odatda bu `storageClassName` yoki hajm |
| 4 | StorageClass bor, provisioner ishlayapti | `kubectl get sc`; provisioner’ning Pod’lari | provisioner’i yo’q class’ni nomlagan PVC abadiy kutadi; `WaitForFirstConsumer` esa **Pod undan foydalanmaguncha Pending** - bu normal |
| 5 | PV `Available`, `Released` emas | `kubectl get pv` | `Released` PV’lar `claimRef` tozalanmaguncha yoki PV qayta yaratilmaguncha qayta ishlatilmaydi |
| 6 | Pod **to’g’ri PVC nomiga** murojaat qilyaptimi | `kubectl get pod -o yaml \| grep -A3 persistentVolumeClaim` | `claimName` ichidagi xato → `persistentvolumeclaim "x" not found` |
| 7 | `hostPath` **o’sha** node’da bormi | `ssh node; ls <path>`; `type: DirectoryOrCreate` | hostPath har bir node’ga xos - boshqa node’ga ko’chgan Pod u yerda hech narsa topmaydi |
| 8 | local PV’dagi `nodeAffinity` | `kubectl describe pv` | Pod faqat nomi ko’rsatilgan node’da ishlay oladi; scheduler buni Events ichida aytadi |
| 9 | ConfigMap/Secret volume | `kubectl get cm,secret -n <ns>`; `items` yoki `subPath` da nomlangan kalit | obyekt yo’q → `MountVolume.SetUp failed` bilan `ContainerCreating` |
| 10 | RWO volume allaqachon boshqa joyda ulangan | boshqa egasini topish uchun `kubectl get pod -A -o wide` | `Multi-Attach error`: oldingi Pod uni hali ushlab turibdi (node o’chiq, Terminating) |
| 11 | ichkaridagi ruxsatlar | `kubectl exec <p> -- ls -ld /data; id` | `securityContext.fsGroup` ni belgilang, yoki image yoza olmaydigan uid ostida ishlayapti |

## Events’ni o’qish

```bash
kubectl get events -n <ns> --sort-by=.lastTimestamp | grep -iE "fail|warn|error"
```

```
Warning  FailedScheduling  pod/web  0/3 nodes are available: pod has unbound immediate PersistentVolumeClaims
Warning  FailedMount       pod/web  MountVolume.SetUp failed for volume "config" : configmap "app-cfg" not found
Warning  FailedAttachVolume pod/web Multi-Attach error for volume "pvc-…" Volume is already used by pod(s) web-old
Warning  ProvisioningFailed pvc/data storageclass.storage.k8s.io "fast" not found
```

Bularning har biri - checklistdagi bitta qator; xabar qaysi biri ekanini
aytadi.

:::exam-tip
Imtihonda checklistni tartib bilan bajaring va birinchi nosozlikda
to’xtang - ko’pincha javob o’sha. Oxirgi qadam har doim bir xil: dastlabki
simptomni qayta hosil qiling (Service’ga `curl`; `kubectl get pod` Running
va Ready; volume’ga fayl yozing), toki tekshiruvchi diagnostikani emas,
tuzatishni ko’rsin.
:::

## O’zingizni tekshiring

1. Client Service’ga nomi orqali yeta olmayapti. Server Pod’dan boshlab
   tashqariga qarab tekshiruvlar tartibini ayting.
2. Binding rejimi `WaitForFirstConsumer` bo’lgan StorageClass bilan PVC
   Pending holatida. Bu muammomi?
3. Pod `Multi-Attach error` deyapti. Bu nimani anglatadi va nimani
   qidirasiz?
