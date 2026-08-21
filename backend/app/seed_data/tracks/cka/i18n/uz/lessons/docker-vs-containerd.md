## Doim eshitib turadigan ikkita nom

Yillar davomida "Docker" butun stekni anglatardi: CLI, demon, image qurish,
image saqlash, jarayonlarni aslida ishga tushiradigan runtime. Kubernetes’ga
esa faqat oxirgi qismi kerak bo’lgan - image’ni tortib olib, konteyner ishga
tushira oladigan narsa - va u buni **Container Runtime Interface (CRI)**
orqali so’raydi.

Docker’ning demoni CRI’da hech qachon nativ gaplashmagan. Kubernetes tarjima
qilish uchun kubelet ichida shim (`dockershim`) olib yurardi. Shu orada
Docker’ning o’zi runtime’ini alohida loyihaga - CRI’da *gaplashadigan*
**containerd** ga ajratib olgan edi. containerd yetilgach, shim’ning mavjud
bo’lishiga sabab qolmadi.

```
kubelet ──CRI──▶ containerd ──▶ runc ──▶ jarayoningiz
          (gRPC)               (OCI)
```

- **containerd** - yuqori darajali runtime: image’larni tortadi, storage va
  snapshot’larni boshqaradi, konteynerlarni nazorat qiladi. Kubelet bilan
  CRI’da gaplashadi.
- **runc** - quyi darajali runtime: fayl tizimi bundle’i va OCI konfiguratsiyasi
  berilganda Linux namespace va cgroup’larini yaratadi hamda jarayonni exec
  qiladi.
- **CRI-O** - faqat Kubernetes uchun qurilgan muqobil yuqori darajali runtime.
  Bir xil shartnoma, boshqa loyiha.

## Uchta CLI

Chalkashlik aynan shu yerda yashaydi. containerd ishlayotgan node’da uchta
vositani topishingiz mumkin va ular bir-birining o’rnini bosmaydi.

| Vosita | Kim bilan gaplashadi | Vazifasi | Nimaga ishlatasiz |
|---|---|---|---|
| `ctr` | containerd | containerd’ning o’z debug CLI’si | deyarli hech narsaga - u qulay emas va production uchun mo’ljallanmagan |
| `nerdctl` | containerd | Docker bilan mos CLI | node’da konteynerlarni `docker` bilan qilganingizday qo’lda ishga tushirish |
| `crictl` | har qanday CRI runtime | CRI debug CLI’si | **kubelet nimani ishga tushirganini ko’rish** - imtihon e’tibor beradigani |

```bash
# Kubelet bu node'da nimani ishlatayotgani - control plane konteynerlari bilan
crictl ps
crictl ps -a                      # tugagan konteynerlarni ham qo'shadi
crictl logs <container-id>        # kubectl logs API server'ga yeta olmaganda
crictl images
crictl pods                       # sandbox'lar (har Pod uchun bittadan)
```

:::exam-tip
API server o’chganda `kubectl` foydasiz, lekin control plane node’da `crictl`
hamon ishlaydi: `crictl ps -a | grep apiserver`, keyin `crictl logs <id>` - u
nega qulaganini shunday o’qiysiz. Bu butun boshli vazifaga arziydigan,
nosozlikni bartaraf etish domenidagi harakat.
:::

`crictl` `/etc/crictl.yaml` orqali sozlanadi:

```yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
```

Agar `crictl` ulana olmasligidan shikoyat qilsa, birinchi tekshiriladigan
narsa - o’sha fayl (yoki `--runtime-endpoint` flagi).

## Image’lar o’zgarmadi

Shovqin ichida yo’qolib ketadigan muhim nuqta: Docker image’i - bu **OCI
image**. containerd uni o’zgartirmasdan ishga tushiradi. Bugun `docker build`
bilan quradigan hamma narsangiz har qanday Kubernetes klasterida ishlayveradi;
yo’qolgani - image formati emas, *runtime* yo’li.

:::note
Docker’siz node’da image qurmoqchi bo’lsangiz `nerdctl build` bor, lekin
klaster node’larida image qurish baribir anti-pattern - bu CI’ning ishi.
:::

## Bu administrator uchun nega muhim

- **Klaster o’rnatishda**: kubeadm’ga `kubeadm init` dan oldin CRI runtime
  mavjud bo’lishi kerak - containerd’ni o’rnatish va sozlash bu yo’l
  xaritasidagi keyingi o’rnatish darsining birinchi qadami.
- **Node nosozligini topishda**: konteyner runtime’i o’lgan `NotReady` node
  `kubectl` tomonidan qaraganda xuddi o’lgan kubelet’day ko’rinadi.
  `systemctl status containerd` va `crictl ps` ularni ajratib beradi.
- **Kubelet loglarini o’qishda**: CRI xatolari soket va runtime nomini aytadi,
  shuning uchun ularni tanib olishingiz kerak.

## O’zingizni tekshiring

1. API server o’chgan. Qaysi buyruq sizga API server konteynerining loglarini
   ko’rsatadi va uni qaysi node’da ishga tushirasiz?
2. containerd va runc orasidagi farq nima?
3. Hamkasbingiz "dockershim olib tashlangani uchun endi Docker image’laridan
   foydalana olmaymiz" deydi. Bu gapning nimasi noto’g’ri?
