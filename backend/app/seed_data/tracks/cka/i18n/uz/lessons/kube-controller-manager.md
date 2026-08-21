## Moslashtirish dvigateli

Kubernetes deklarativ: siz xohlagan holatni yozib qo’yasiz va *nimadir*
haqiqatni unga moslashtirib turadi. O’sha nimadir - **kontroller**, ya’ni API
server orqali bir turdagi obyektni kuzatadigan, kutilgan holatni haqiqiysi
bilan solishtiradigan va farq ustida harakat qiladigan tsikl. Deployment’ni 5
ga masshtablang - kontroller ikkita Pod yaratadi. Node yo’qolsa, kontroller uni
belgilaydi va undagilarni qayta joylashtiradi.

Bunday tsikllar o’nlab. **kube-controller-manager** - o’rnatilgan tsikllarning
hammasini ishga tushiradigan yagona jarayon:

| Kontroller | Nimani kuzatadi | Nimani ta’minlaydi |
|---|---|---|
| Node | Node’lar va ularning heartbeat’lari | jim qolgan node `NotReady` bo’ladi, so’ng uning Pod’lari evict qilinadi |
| Replication / ReplicaSet | ReplicaSet’lar | kerakli sondagi Pod’lar mavjud bo’ladi |
| Deployment | Deployment’lar | ReplicaSet’lar yaratiladi va to’g’ri tartibda rollout qilinadi |
| Endpoints / EndpointSlice | Service’lar va Pod’lar | Service’ning endpoint ro’yxati uning selektoriga mos keladi |
| ServiceAccount va Token | namespace’lar, SA’lar | har bir namespace’da default SA bo’ladi |
| Namespace | Namespace’lar | namespace’ni o’chirish uning tarkibini ham o’chiradi |
| Job, CronJob, DaemonSet, StatefulSet | o’z turlarini | har biri nomi aytgan ishni qiladi |
| PersistentVolume binder | PVC’lar va PV’lar | claim’lar volume topadi |
| Garbage collector | owner reference’lar | yetim qolgan bolalar o’chiriladi |

Bitta binary, ko’p tsikl - shunda har biriga alohida deployment, leader saylovi
va sertifikatlar kerak bo’lmaydi.

## U qanday ishlaydi

kubeadm klasterlarida yana bir static Pod:

```bash
cat /etc/kubernetes/manifests/kube-controller-manager.yaml
kubectl get pods -n kube-system | grep controller-manager
```

```yaml
- kube-controller-manager
- --kubeconfig=/etc/kubernetes/controller-manager.conf   # API server bilan qanday gaplashadi
- --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
- --cluster-signing-key-file=/etc/kubernetes/pki/ca.key  # u CSR imzolovchisi
- --root-ca-file=/etc/kubernetes/pki/ca.crt
- --service-account-private-key-file=/etc/kubernetes/pki/sa.key
- --controllers=*,bootstrapsigner,tokencleaner
- --leader-elect=true
- --node-monitor-period=5s
- --node-monitor-grace-period=40s
- --use-service-account-credentials=true
```

Ulardan ikkitasiga alohida e’tibor berish kerak.

- `--cluster-signing-cert-file` / `-key-file`: CertificateSigningRequest’ni
  tasdiqlaganingizda (sertifikatlar darsi), uni klaster CA’si bilan
  imzolaydigan **aynan shu** komponent. Agar CSR’lar tasdiqlangan holda tursa-yu,
  hech qachon berilmasa, shu yerga qarang.
- `--node-monitor-grace-period`: node `NotReady` deb belgilanguncha qancha vaqt
  jim tura oladi. Kubelet’ning heartbeat oralig’i bilan birgalikda u klaster
  o’lgan node’ga qanchalik tez javob berishini belgilaydi.

:::exam-tip
Controller manager ham, scheduler ham `--leader-elect=true` bilan ishlaydi: bir
nechta control plane’li klasterda barcha replikalar ishlaydi, lekin faqat leader
harakat qiladi. Leaderni yo’qotish bir necha soniyalik saylovga tushadi,
to’g’rilikka emas.
:::

## U buzilganda qanday ko’rinadi

Controller manager o’lganda hech narsa *darhol* ishlashdan to’xtamaydi, uni
xavfli qiladigan narsa ham shu. API server javob beradi, kubectl joyida, mavjud
Pod’lar ishlashda davom etadi - lekin:

- `kubectl scale deployment web --replicas=5` sonni o’zgartiradi va **hech
  qanday Pod paydo bo’lmaydi**;
- ReplicaSet’ning o’chirilgan Pod’i **almashtirilmaydi**;
- yangi CSR’lar tasdiqlangan holda qoladi, lekin hech qachon sertifikat olmaydi;
- yangi namespace’da **default ServiceAccount bo’lmaydi**, shuning uchun undagi
  Pod’lar yaratilmaydi.

```bash
kubectl get pods -n kube-system | grep controller-manager   # CrashLoopBackOff?
kubectl logs -n kube-system kube-controller-manager-controlplane | tail
kubectl describe pod -n kube-system kube-controller-manager-controlplane | tail -20
```

Imtihondagi tipik nosozliklar: manifestda noto’g’ri yozilgan image yoki command,
noto’g’ri `--kubeconfig` yo’li, `/etc/kubernetes/pki` ostidagi mavjud bo’lmagan
sertifikat yo’li yoki noto’g’ri katalogdan ulangan `hostPath` volume.

:::tip
"Masshtablash hech narsa qilmayapti" - bu controller manager. "Pod’lar Pending’da
qolyapti" - bu scheduler. "kubectl osilib qolyapti" - bu API server. Uchta
alomat, uchta komponent - bu moslikni yodlab oling.
:::

## O’zingizni tekshiring

1. Deployment’ni masshtablaysiz, son yangilanadi, lekin hech qanday Pod paydo
   bo’lmaydi. Qaysi komponentga shubha qilasiz va birinchi buyruq nima?
2. Tasdiqlangan CertificateSigningRequest’ni aslida qaysi komponent imzolaydi?
3. Nega controller manager bir daqiqa o’chib turishi mumkin va ishlab turgan
   biror ilova buni sezmaydi?
