## Hammani qo’rqitgan e’lon

2020-yil oxirida Kubernetes loyihasi `dockershim` - kubelet’ning Kubernetes va
Docker demoni orasida tarjima qiladigan qismi - eskirgan deb e’lon qildi, va
Kubernetes 1.24 da u butunlay olib tashlandi. "Kubernetes Docker’dan voz
kechdi" degan sarlavha butun dunyoni aylanib chiqdi va deyarli hamma joyda
noto’g’ri tushunildi.

Aslida olib tashlangani: **kubelet konteynerlarni ishga tushirishning bitta
yo’li**.

Olib tashlanmagani: Docker image’lari, Dockerfile’lar, `docker build`, Docker
Desktop, Docker Hub yoki kimningdir ishlab turgan workload’i.

## Node’da aslida nima o’zgardi

1.24 dan oldin node Docker demonini ishlata olardi va kubelet u bilan shim
orqali gaplashardi:

```
kubelet ──dockershim──▶ dockerd ──▶ containerd ──▶ runc
```

E’tibor bering, containerd allaqachon zanjirda edi - Docker’ning o’zi undan
foydalanardi. Shim shunchaki bitta bekat qo’shardi. 1.24 dan keyin kubelet
containerd bilan to’g’ridan-to’g’ri gaplashadi:

```
kubelet ──CRI──▶ containerd ──▶ runc
```

Natijada node boshqacha emas, *kamroq* dasturiy ta’minot ishlatadi.

## Siz, administrator, nima qilishingiz kerak edi

Agar node Docker’ni runtime sifatida ishlatgan bo’lsa, migratsiya shunday edi:

1. containerd’ni o’rnating (odatda allaqachon mavjud - Docker unga bog’liq) va
   `/etc/containerd/config.toml` da uning CRI plaginini yoqing.
2. Kubelet’ni containerd soketiga yo’naltiring:
   `--container-runtime-endpoint=unix:///run/containerd/containerd.sock`.
3. Node’ni drain qiling, kubelet’ni qayta ishga tushiring, uncordon qiling.

Node’larda `dockerd` ni saqlab qolmoqchi bo’lganlar uchun Docker’ning o’z
javobi - Mirantis qo’llab-quvvatlaydigan tashqi shim **cri-dockerd**. U
ishlaydi, lekin deyarli hech kimga kerak emas.

:::warning
Zamonaviy node’da `docker ps` u yerda ishlayotgan Pod’lar haqida **hech narsa**
ko’rsatmaydi - kubelet Docker’dan foydalanmayapti. "Node’da bir docker ps qilib
ko’ray" odati - tashlash kerak bo’lgani. `crictl ps` dan foydalaning.
:::

## Imtihonda u qayerda hamon uchraydi

- Klaster o’rnatish vazifalari containerd’ni nazarda tutadi; siz Docker’ni
  emas, uni sozlaysiz.
- Nosozlikni bartaraf etish vazifalari konteyner runtime’ini to’xtatib node’ni
  `NotReady` holatga tushirishi mumkin; yechim - Docker’ga aloqador biror narsa
  emas, `systemctl start containerd`.
- Image’lar haqidagi savollar o’zgarmagan: image nomlari, tag’lar, pull policy
  va shaxsiy registry’lar doim qanday ishlagan bo’lsa, xuddi shunday ishlaydi.

:::tip
Agar oldingizda Dockerfile tursa, bu yerdagi hech narsa unga tegishli emas - u
hamon OCI image quradi va o’sha image hamon hamma joyda ishlaydi. Eskirish
node’dagi demon haqida edi, hech qachon artefakt haqida emas.
:::

## O’zingizni tekshiring

1. Kubernetes 1.24 aynan nimani olib tashladi, bitta gapda ayting?
2. Node `NotReady` ko’rsatyapti; undagi `docker ps` hech narsa chiqarmaydi.
   Nega bu hech narsani isbotlamaydi va uning o’rniga nimani ishga tushirasiz?
3. `cri-dockerd` nima va u sizga qachon haqiqatan kerak bo’ladi?
