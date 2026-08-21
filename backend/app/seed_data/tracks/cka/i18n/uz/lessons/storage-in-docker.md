## Docker nimalarni qayerda saqlaydi

```bash
ls /var/lib/docker
# containers  image  overlay2  volumes  network  plugins  ...
```

Docker saqlaydigan hamma narsa `/var/lib/docker` ostida yotadi: image
qatlamlari `image/` va `overlay2/`’da, konteynerning yoziladigan qatlami
`containers/`’da, nomlangan volume’lar `volumes/`’da. containerd ishlaydigan
Kubernetes node’larida ularning ekvivalenti `/var/lib/containerd` va
`/run/containerd` ostida; tushunchalar bir xil va keyingi CSI darslari shular
ustiga quriladi.

## Image’lar - qatlamlar

```dockerfile
FROM ubuntu               # 1-qatlam: asosiy fayl tizimi
RUN apt-get update && apt-get install -y python3   # 2-qatlam: paketlar
COPY app.py /app/         # 3-qatlam: sizning kodingiz
ENTRYPOINT ["python3", "/app/app.py"]              # 4-qatlam: faqat metadata
```

Har bir ko’rsatma faqat o’zgargan narsani saqlaydigan **read-only qatlam**
qo’shadi. Qatlamlar kontent bo’yicha adreslanadi va ulashiladi: o’sha hostdagi
ikkinchi `FROM ubuntu` image’i 1-qatlamni diskdan va keshdan qayta ishlatadi.
Shuning uchun faqat `app.py` o’zgargandan keyingi qayta qurish tez bo’ladi -
1-2 qatlamlar keshda - va shuning uchun Dockerfile’larni "sekin o’zgaradigani
birinchi, tez o’zgaradigani oxirgi" tartibida yozish muhim.

## Konteyner qatlami

Konteyner ishga tushganda Docker image’ning read-only qatlamlari ustiga
**yupqa yoziladigan qatlam** qo’yadi. Jarayon yozadigan hamma narsa - log
fayllar, vaqtinchalik fayllar, o’zgartirilgan konfiguratsiya - o’sha yerga
boradi. Ikkita oqibat:

- Image hech qachon o’zgarmaydi. Bitta image’dan ishga tushgan ikki
  konteynerning har biri o’zining yoziladigan qatlamini oladi.
- **Yoziladigan qatlam konteyner bilan birga o’ladi.** `docker rm` - va
  ma’lumot yo’q. Ishlash paytida image yo’liga fayl yozish -
  **copy-on-write**: fayl yoziladigan qatlamga nusxalanadi, image’dagi
  nusxasiga tegilmaydi.

"Konteynerim qayta ishga tushganda ma’lumotini yo’qotdi" degani nega bug emas
va volume’lar nega mavjud - sababi shu.

## Volume va bind mount

Konteynerga doimiy storage berishning ikki yo’li:

```bash
docker volume create data_volume
docker run -v data_volume:/var/lib/mysql mysql            # VOLUME mount: /var/lib/docker ostidagi Docker boshqaradigan katalog
docker run -v /data/mysql:/var/lib/mysql mysql            # BIND mount: hostning istalgan yo'li
docker run --mount type=bind,source=/data/mysql,target=/var/lib/mysql mysql   # o'shaning ochiq shakli
```

| | Volume mount | Bind mount |
|---|---|---|
| hostda qayerda | `/var/lib/docker/volumes/<name>/_data` | siz aytgan joyda |
| kim boshqaradi | Docker (`docker volume ls/rm/inspect`) | siz |
| hostlar orasida ko’chma | bind mount’dan ortiq emas - baribir lokal disk | yo’q |

Ikkalasi ham konteynerdan keyin qoladi. Hech biri hostdan keyin qolmaydi -
Kubernetes’ning persistent volume modeli hal qiladigan muammo aynan shu.

## Storage driver’lar

Qatlamlashning o’zi - read-only qatlamlar va bitta yoziladigan qatlamni yagona
fayl tizimi ko’rinishiga yig’ish - **storage driver**ning ishi: zamonaviy
Linuxda `overlay2`, tarixan `aufs`, `devicemapper`, `btrfs`, `zfs`. Driver har
bir host uchun tanlanadi va siz u haqda kamdan-kam o’ylaysiz; lekin u amalga
oshiradigan qatlamli dizayn image tortishni bosqichma-bosqich, konteyner ishga
tushishini esa bir zumda qiladi.

```bash
docker info | grep "Storage Driver"
# Storage Driver: overlay2
```

:::tip
Storage driver’lar **image qatlamlari** bilan ishlaydi; volume driver’lar
(keyingi dars) esa **volume’lar** bilan. Bir xil "driver" so’zi, ikkita boshqa
plugin nuqtasi - ularni ajratib turing, shunda keyingi CSI darsi tushunarli
bo’ladi.
:::

## Bu nega Kubernetes kursida

Yuqoridagi hamma narsa to’g’ridan-to’g’ri moslashadi:

| Docker | Kubernetes |
|---|---|
| image qatlamlari, storage driver | o’shaning o’zi, har bir node’dagi containerd ichida |
| konteynerning yoziladigan qatlami | o’shaning o’zi: konteyner qayta ishga tushganda yo’qoladi |
| `-v name:/path` volume | `emptyDir` (har Pod uchun) / `hostPath` (node katalogi) |
| volume driver’lar | CSI va PersistentVolume’lar |

`Pod deleted, data gone` hayrati - bu Kubernetes shlyapasini kiygan o’sha
Docker hayrati; keyingi darslar - undan chiqish yo’llari.

## O’zingizni tekshiring

1. Konteyner o’chirilganda uning ichida `/var/log/app.log`’ga yozilgan faylga
   nima bo’ladi - va nega?
2. Volume mount va bind mount orasidagi farq nima?
3. Ikkita image ham `FROM ubuntu` bilan boshlanadi. Diskda Ubuntu qatlamining
   nechta nusxasi bor va bu qayta qurish uchun nega muhim?
