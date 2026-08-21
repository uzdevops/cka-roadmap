## Mock imtihon 1

Ikki soat. O’n ikkita vazifa. Umumiy og’irlik 100. Ularni o’z
klasteringizda bajaring (ikki node’li kubeadm yoki kind klasteri yetarli;
vazifada `node01` kerak bo’lgan joyda o’z worker’ingizning nomini
ishlating). Keyingisiga o’tishdan oldin har birini tekshiring. Yechimlar
keyingi darsda - soat to’xtamaguncha uni ochmang.

Avval sozlang:

```bash
alias k=kubectl
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"
```

---

**1.** (4) `nginx:alpine` image’idan foydalanib `nginx-pod` nomli Pod
joylashtiring.

**2.** (4) `redis:alpine` image’idan foydalanib, `tier=msg` label’i bilan
`messaging` nomli Pod joylashtiring.

**3.** (4) `apx-x9984574` nomli Namespace yarating.

**4.** (6) Node’lar ro’yxatini JSON formatida oling va uni
`/opt/outputs/nodes-z3444kd9.json` fayliga saqlang.

**5.** (8) `messaging` Pod’ini klaster ichida `6379` portda ochish uchun
`messaging-service` nomli Service yarating.

**6.** (8) `kodekloud/webapp-color` image’idan foydalanib, `2` replikali
`hr-web-app` nomli Deployment yarating.

**7.** (10) Control plane node’da `busybox` image’i va `sleep 1000`
buyrug’idan foydalanadigan `static-busybox` nomli static Pod yarating.

**8.** (6) `finance` namespace’ida `redis:alpine` image’i bilan `temp-bus`
nomli Pod yarating.

**9.** (12) `orange` nomli Pod ishlamayapti. Uni tuzating. (Mock’dan oldin
uni quyidagi manifest bilan yarating - xato ataylab qo’yilgan.)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: orange
spec:
  initContainers:
  - name: init-myservice
    image: busybox
    command: ['sh', '-c', 'sleeeep 2;']
  containers:
  - name: orange-container
    image: busybox:1.28
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
```

**10.** (10) `hr-web-app` Deployment’ini `hr-web-app-service` nomli Service
sifatida oching: turi `NodePort`, ilova porti `8080`, node porti `30082`.

**11.** (8) Har bir node’ning `osImage`ini olish uchun JSONPath’dan
foydalaning va uni `/opt/outputs/nodes_os_x43kj56.txt`ga saqlang.

**12.** (10) `pv-analytics` nomli PersistentVolume yarating: storage
`100Mi`, kirish rejimi `ReadWriteMany`, host path `/pv/data-analytics`.

**13.** (10) `frontend` namespace’idagi `web-front` nomli Deployment yangi
image’ni rollout qilyapti va uning Pod’lari qotib qolgan. Uni oldingi
ishlaydigan revision’ga rollback qiling va barcha replikalar Available
ekanini tasdiqlang.
(Mock’dan oldin: `kubectl create ns frontend; kubectl create deploy web-front
--image=nginx:1.25 -n frontend --replicas=3; kubectl set image deploy
web-front nginx=nginx:1.99-doesnotexist -n frontend`.)

---

Tugagach: har bir vazifa bo’yicha o’zingizni baholang, og’irliklar
ko’rsatilganidek, to’liq ball faqat aynan mos yakuniy holat uchun. Keyin
yechimlar darsi.

:::exam-tip
Bu o’n uchta vazifadan beshtasi - bitta imperativ buyruq. Ulardan
birortasi sizdan to’qson soniyadan ko’proq vaqt olgan bo’lsa, keyingi
soatingiz tezlik mashqlari darsiga ketadi.
:::

## O’zingizni tekshiring

1. Birinchi o’tishda qaysi vazifalarni o’tkazib yubordingiz va ularga
   qaytdingizmi?
2. Bajargan har bir vazifangiz uchun uni **tekshirish** maqsadida qaysi
   buyruqni ishlatdingiz?
3. Qaysi vazifa eng ko’p vaqt oldi va bu bilim, navigatsiya yoki tezlik
   bo’shlig’i edimi?
