## kubeadm nima qiladi va nima qilmaydi

kubeadm - klasterni eng yaxshi amaliyotdagi sukut qiymatlari bilan ko’taruvchi
upstream vosita. Uning qamrovi ataylab tor:

| kubeadm qiladi | kubeadm qilmaydi |
|---|---|
| node’ni preflight tekshiruvidan o’tkazish | mashinalarni tayyorlash |
| CA va barcha sertifikatlarni generatsiya qilish | konteyner runtime o’rnatish |
| admin va komponentlar uchun kubeconfig yozish | CNI o’rnatish yoki sozlash |
| etcd, API server, controller manager, scheduler uchun static Pod manifestlarini yozish | HA uchun load balancer sozlash |
| kubelet’ni to’g’ri konfiguratsiya bilan ishga tushirish | dashboard, metrika, ingress o’rnatish |
| CoreDNS va kube-proxy’ni deploy qilish | OS yoki paketlarni boshqarish |
| bootstrap token’lar va join buyrug’ini yaratish | |
| control plane va kubelet konfiguratsiyalarini `upgrade` qilish | |

O’ng ustundagi hamma narsa - sizniki, oldin yoki keyin.

## Tartib

```
1. har bir node:     OS tayyorgarligi (swap off, sysctl'lar, modullar) -> konteyner runtime -> kubeadm, kubelet, kubectl
2. birinchi control plane:  kubeadm init
3. admin mashinasi:  admin.conf nusxasini oling -> kubectl ishlaydi
4. klaster:          CNI o'rnating  (node'lar Ready bo'ladi)
5. qolgan node'lar:  kubeadm join   (worker'lar; qo'shimcha control plane uchun --control-plane)
6. tekshirish:       kubectl get nodes, get pods -A
```

CNI qadami init va join orasida turishining sababi bor: tarmoq plugini paydo
bo’lmaguncha node’lar `NotReady` bo’ladi va CoreDNS `Pending` bo’lib turadi;
undan oldin worker’larni qo’shishga ruxsat bor, lekin bu chalkashtiradi.

## init, phase’lar bo’yicha

`kubeadm init` **phase**’lar ro’yxatini bajaradi va ularning har birini alohida
ishga tushirish mumkin (`kubeadm init phase <name>`) - bu keyinroq bitta
narsani qayta generatsiya qilish uchun foydali:

```
preflight            tekshiruvlar: 2 CPU, swap, portlar, runtime, noyob ID'lar
certs                CA, apiserver, apiserver-kubelet-client, etcd/*, front-proxy, sa.key
kubeconfig           admin.conf, kubelet.conf, controller-manager.conf, scheduler.conf
kubelet-start        /var/lib/kubelet/config.yaml ni yozadi va kubelet'ni ishga tushiradi
control-plane        apiserver, controller-manager, scheduler uchun static Pod manifestlari
etcd                 etcd uchun static Pod manifesti (stacked)
upload-config        konfiguratsiyani kubeadm-config ConfigMap'ida saqlaydi
upload-certs         (--upload-certs bilan) HA join'lari uchun sertifikatlarni Secret'ga shifrlaydi
mark-control-plane   node'ga label va taint qo'yadi
bootstrap-token      join token'i va unga tegishli RBAC'ni yaratadi
kubelet-finalize     kubelet sertifikatini rotatsiya qiladi
addon                CoreDNS va kube-proxy'ni deploy qiladi
```

```bash
kubeadm init phase certs apiserver --apiserver-cert-extra-sans=lb.example.com   # BITTA sertifikatni qayta generatsiya qilish
kubeadm init phase upload-certs --upload-certs                                   # control plane qo'shish uchun yangi certificate key
kubeadm config print init-defaults                                                # konfiguratsiya faylining ko'rinishi
```

## Siz aslida beradigan flaglar

```bash
kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \              # o'rnatadigan CNI'ingizga MOS kelishi SHART
  --apiserver-advertise-address=192.168.1.10 \     # API server tinglaydigan IP (ko'p NIC'li node'lar)
  --control-plane-endpoint=lb.example.com:6443 \   # HA uchun yoki kelajakdagi HA uchun
  --upload-certs                                   # HA join'lari uchun
```

Yoki konfiguratsiya fayli (`kubeadm init --config kubeadm-config.yaml`) - qolgan
hamma narsani shu orqali belgilanadi: kubelet konfiguratsiyasi, API server
uchun qo’shimcha argumentlar, tashqi etcd, boshqa service CIDR.

## join

Uni `init` chiqaradi; u 24 soatda muddati tugaydi:

```bash
kubeadm join 192.168.1.10:6443 --token abcdef.0123456789abcdef \
  --discovery-token-ca-cert-hash sha256:1234...
```

- `token` - **bootstrap token**: qo’shilayotgan node’ni o’z sertifikatini
  olishga yetadigan muddatga autentifikatsiya qiladi.
- `discovery-token-ca-cert-hash` - qo’shilayotgan node o’zi to’g’ri klaster
  bilan gaplashayotganini tekshira olishi uchun (u berilgan CA’ni xeshlaydi va
  solishtiradi).

```bash
kubeadm token list
kubeadm token create --print-join-command        # istalgan paytda yangi token va to'liq buyruq
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex   # xeshni qo'lda hisoblash
```

Qo’shilayotgan node’da `join` preflight’ni bajaradi, CA’ni oladi, o’z
kubelet’i uchun CSR yuboradi (token orqali avtomatik tasdiqlanadi),
`kubelet.conf` ni yozadi va kubelet’ni ishga tushiradi. Control plane join’i
(`--control-plane --certificate-key`) qo’shimcha ravishda umumiy
sertifikatlarni tortib oladi va o’zining static Pod manifestlarini yozadi.

:::exam-tip
join paytidagi ikkita nosozlik takrorlanib turadi: token **muddati tugagan**
(control plane’da `kubeadm token create --print-join-command`) va qo’shilayotgan
node kubelet’ida oldingi urinishdan qolgan eski `/etc/kubernetes/kubelet.conf`
turibdi (avval `kubeadm reset`). Va `init` dan keyin boshqa hamma narsadan
oldin **admin.conf nusxasini oling** - control plane’dagi `kubectl` shusiz
ishlamaydi.
:::

## reset

```bash
kubeadm reset -f        # SHU node'dagi init/join'ni bekor qiladi: kubelet'ning static Pod'larini to'xtatadi, /etc/kubernetes/* ni o'chiradi
rm -rf /etc/cni/net.d $HOME/.kube/config
iptables -F && iptables -t nat -F && iptables -X    # kube-proxy qoidalari qolib ketadi
```

`reset` - muvaffaqiyatsiz init’ni qayta urinish yoki node’ni boshqa maqsadga
o’tkazish usuli. U node’ni klasterning ko’rinishidan olib tashlamaydi - buni
control plane’da `kubectl delete node <name>` qiladi.

## O’zingizni tekshiring

1. kubeadm sizga qoldiradigan uchta narsani ayting va ularning har biri ish
   oqimining qaysi nuqtasida bajarilishini ham.
2. join buyrug’idagi ikkita qiymat mos ravishda nima uchun kerak?
3. Kechagi init bergan join buyrug’i bugun ishlamayapti. Nega va nima ishga
   tushirasiz?
