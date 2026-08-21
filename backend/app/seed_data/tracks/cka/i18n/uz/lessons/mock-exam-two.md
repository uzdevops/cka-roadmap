## Mock imtihon 2

Ikki soat. O’nta vazifa. Umumiy og’irlik 100. Mock 1’dan qiyinroq: bir
qatorli buyruqlar kamroq, YAML ko’proq, ikkita vazifa node talab qiladi.
Har bir yakuniy holatni tekshiring.

```bash
alias k=kubectl; export do="--dry-run=client -o yaml"
```

---

**1.** (12) etcd ma’lumotlar bazasining snapshot’ini oling va uni
`/opt/etcd-backup.db`ga saqlang. (Sertifikatlarni etcd static Pod’ining
manifestidan oling.)

**2.** (8) `redis:alpine` image’idan foydalanib `redis-storage` nomli Pod
yarating; unda `/data/redis`ga mount qilingan, `redis-storage` nomli
`emptyDir` turidagi volume bo’lsin.

**3.** (8) `busybox:1.28` image’idan foydalanib, `sleep 4800` ni
bajaradigan `super-user-pod` nomli Pod yarating; uning konteyneriga
`SYS_TIME` capability’si qo’shilgan bo’lsin.

**4.** (10) `my-pvc` nomli PersistentVolumeClaim mavjud (avval uni
yarating: 10Mi RWO PVC va unga mos `/tmp/pv1`dagi hostPath PV `pv-1`).
`nginx` image’idan foydalanib, bu claim’ni `/data`ga mount qiladigan
`use-pv` nomli Pod yarating.

**5.** (10) `nginx:1.16` image’idan foydalanib, `1` replikali
`nginx-deploy` nomli Deployment yarating. So’ng uni rolling update bilan
`nginx:1.17`ga yangilang va o’zgarish sababini `nginx 1.17` deb yozib
qo’ying.

**6.** (14) `development` namespace’i uchun `john` foydalanuvchisini
yarating: shaxsiy kalit va CSR generatsiya qiling, `system:authenticated`
guruhi hamda `kubernetes.io/kube-apiserver-client` signer’i bilan
`john-developer` nomli CertificateSigningRequest yuboring, uni tasdiqlang,
`development` ichida `pods` ustida `create, list, get, update, delete`
amallariga ruxsat beruvchi `developer` nomli Role yarating va uni
`john-developer` RoleBinding’i orqali `john`ga bog’lang.
`kubectl auth can-i` bilan tekshiring.

**7.** (12) `nginx-resolver` nomli `nginx` Pod’ini yarating va uni
`nginx-resolver-service` Service’i bilan klaster ichida oching. Service
ham, Pod ham `busybox:1.28` Pod’idan yechilishini sinang; Service
qidiruvini `/root/CKA/nginx.svc`ga, Pod qidiruvini `/root/CKA/nginx.pod`ga
yozib qo’ying.

**8.** (10) `node01` worker node’ida `nginx` image’idan foydalanib
`nginx-critical` nomli static Pod yarating. U o’chirilsa qayta
yaratilishini ta’minlang.

**9.** (8) `backend` namespace’idagi `api` Deployment’i har bir node’da,
jumladan control plane node’larida ham, aynan bitta Pod ishlatishi kerak.
Uni bir xil Pod template’i bilan (image `nginx:alpine`, label `app=api`)
to’g’ri workload turiga o’tkazing. (Avval Deployment’ni 1 replika bilan
yarating.)

**10.** (8) `LOG_LEVEL=debug` va `MODE=test` bilan `app-config` ConfigMap’i
va ConfigMap’ning **barcha** kalitlarini muhit o’zgaruvchilari sifatida
yuklaydigan `cm-pod` Pod’ini (image `busybox:1.28`, buyruq `env;
sleep 3600`) yarating. `kubectl logs` bilan tekshiring.

---

Baholang, keyin yechimlar.

:::exam-tip
1, 6 va 7-vazifalar - mashq qilmagan bo’lsangiz, vaqtingizni yeydiganlari.
Har biri o’ttiz soniyadan kam vaqtda topa olishingiz kerak bo’lgan bitta
hujjat sahifasi: "Operating etcd clusters" (backup), "Certificate Signing
Requests" (john foydalanuvchisi), "DNS for Services and Pods" (resolver).
Qidiruv so’zlarini biling.
:::

## O’zingizni tekshiring

1. O’nta vazifadan qaysi biri `ssh` talab qildi va `exit` qilishni
   esladingizmi?
2. 6-vazifada john `development`da Pod yarata olishini va `default`da
   yarata olmasligini qaysi buyruq isbotladi?
3. Qaysi vazifaning hujjat sahifasini topish eng ko’p vaqt oldi va qaysi
   qidiruv so’zi uni tezroq topib berardi?
