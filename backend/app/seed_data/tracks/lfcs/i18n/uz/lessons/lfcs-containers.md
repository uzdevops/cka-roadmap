## Linux host’ida konteynerlar

Konteyner - bu **sizning** kernel’ingizdagi process; u namespace’lar bilan
izolyatsiya qilingan (process’lar, tarmoq, mount’lar, user’larning o’z
ko’rinishi) va cgroup’lar bilan cheklangan (CPU, xotira). Guest kernel
yo’q, boot yo’q - shuning uchun u VM soniyalarda ishga tushadigan joyda
millisekundlarda ishga tushadi.

Maqsadlarda ikkita runtime uchraydi: **docker** va **podman**. Buyruqlar
ataylab bir xil; podman daemon’siz ishlaydi va rootless bo’la oladi, RHEL’da
esa u sukut bo’yicha.

```bash
sudo apt install docker.io      # yoki: sudo dnf install podman
sudo systemctl enable --now docker
docker version; podman version
alias docker=podman             # quyidagi har bir buyruq ikkalasi bilan ham ishlaydi
```

## Image’lar va konteynerlar

**Image** - bu faqat o’qish uchun fayl tizimi va metadata; **konteyner** -
uning ishlayotgan (yoki to’xtatilgan) nusxasi, ustida yoziladigan qatlam
bilan.

```bash
docker pull nginx:1.27-alpine        # image olib keladi (doim tag'ni qadang, :latest ga tayanmang)
docker images                        # lokal image'lar
docker search nginx
docker rmi nginx:1.27-alpine         # image'ni o'chiradi
docker image prune -a                # ishlatilmayotgan image'larni o'chiradi
```

## Ishga tushirish

```bash
docker run -d --name web -p 8080:80 nginx:1.27-alpine
#   -d fonda      --name barqaror nom      -p HOSTPORT:CONTAINERPORT
docker run -it --rm alpine:3.20 sh          # interaktiv, chiqishda o'chiriladi
docker run -d --name db \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  --restart=unless-stopped \
  --memory=512m --cpus=1 \
  postgres:16
docker run --rm -v /srv/data:/data:ro alpine ls /data      # bind mount, faqat o'qish uchun
```

| Flag | Nima qiladi |
|---|---|
| `-d` | fonda |
| `-it` | interaktiv terminal |
| `--rm` | konteyner chiqqanda uni o’chiradi |
| `--name` | tasodifiy nom o’rniga nom beradi |
| `-p 8080:80` | host portini → konteyner portiga chiqaradi |
| `-e K=V` | muhit o’zgaruvchisi |
| `-v name:/path` | **nomlangan volume** (boshqariladi, saqlanib qoladi) |
| `-v /host:/path` | **bind mount** (host katalogi); faqat o’qish uchun `:ro` qo’shing |
| `--restart` | `no`, `on-failure`, `always`, `unless-stopped` |
| `--memory`, `--cpus` | limitlar (cgroup’lar) |
| `--network` | qaysi tarmoqqa qo’shilishi |
| `-u 1000:1000` | root o’rniga uid sifatida ishlaydi |

## Boshqarish

```bash
docker ps                       # ishlayotganlari
docker ps -a                    # to'xtatilganlari bilan birga
docker logs web; docker logs -f --tail 50 web
docker exec -it web sh          # ISHLAYOTGAN konteyner ichidagi shell
docker exec web nginx -t
docker stop web; docker start web; docker restart web
docker rm web                   # to'xtatilgan konteynerni o'chiradi; -f majburlaydi
docker inspect web | less       # hammasi: IP, mount'lar, env, holat
docker stats                    # konteyner bo'yicha jonli CPU/xotira
docker top web
docker cp web:/etc/nginx/nginx.conf ./        # fayllarni ichkariga yoki tashqariga nusxalaydi
docker port web
docker system df; docker system prune         # nima disk band qilyapti; tozalash
```

## Ma’lumot: volume’lar va bind mount’lar

Konteynerning yoziladigan qatlami konteyner bilan birga yo’qoladi. Omon
qolishi kerak bo’lgan hamma narsa volume’ga tushadi.

```bash
docker volume create pgdata
docker volume ls; docker volume inspect pgdata
docker run -d -v pgdata:/var/lib/postgresql/data postgres:16     # nomlangan volume: joyini docker boshqaradi
docker run -d -v /srv/www:/usr/share/nginx/html:ro nginx         # bind mount: yo'lni siz tanlaysiz
docker volume rm pgdata
```

Ma’lumotlar bazasi va ilova holati uchun nomlangan volume’lar; config
fayllari va host’da tahrirlaydigan kontent uchun bind mount’lar.

## Tarmoq

```bash
docker network ls                                   # bridge, host, none
docker network create appnet
docker run -d --name db --network appnet postgres:16
docker run -d --name api --network appnet -p 8080:8080 myapi     # db ga "db" nomi orqali yetadi
docker network inspect appnet
```

User tomonidan yaratilgan tarmoqda konteynerlar bir-birini **nom bo’yicha**
topadi - sukut bo’yicha bridge o’rniga tarmoq yaratishning sababi ham shu.

## Image qurish

```dockerfile
FROM alpine:3.20
RUN apk add --no-cache python3
WORKDIR /app
COPY app.py .
EXPOSE 8000
USER 1000
CMD ["python3", "app.py"]
```

```bash
docker build -t myapp:1.0 .
docker run -d -p 8000:8000 myapp:1.0
docker tag myapp:1.0 registry.example.com/myapp:1.0
docker push registry.example.com/myapp:1.0
docker save myapp:1.0 | gzip > myapp.tar.gz         # image'ni registry'siz ko'chirish
docker load < myapp.tar.gz
```

## Konteynerlar service sifatida

```bash
# podman: ishlayotgan konteyner uchun systemd unit'i generatsiya qiladi
podman generate systemd --new --name web > /etc/systemd/system/container-web.service
sudo systemctl daemon-reload && sudo systemctl enable --now container-web
# docker: --restart=unless-stopped dan yoki ExecStart=/usr/bin/docker start -a web bo'lgan unit'dan foydalaning
```

Rootless podman (`podman` oddiy user sifatida, konteynerlar o’zingizning
user namespace’ingizda) - docker’ning root daemon’idan xavfsizlik
jihatidan farqi shu; qaysi birida ekaningizni `podman info | grep rootless`
aytadi.

:::warning
`-v /:/host` ham, `--privileged` ham, user’ni `docker` guruhiga qo’shish ham
- barchasi root berish bilan teng: docker daemon’i root sifatida ishlaydi va
siz so’ragan hamma narsani mount qiladi. `docker` guruhi a’zoligini parolsiz
sudo deb biling va mos joyda rootless podman’ni afzal ko’ring.
:::

:::exam-tip
Kuting: "X image’ini Y nomli konteyner sifatida ishga tushiring, A portini
B ga chiqaring, V volume’ini /path ga mount qiling va u avtomatik qayta
ishga tushishiga ishonch hosil qiling". Bu bitta
`docker run -d --name Y -p A:B -v V:/path --restart=unless-stopped
X`. `docker ps`, `docker inspect` va `curl localhost:A` bilan tekshiring.
:::

## O’zingizni tekshiring

1. Image bilan konteyner o’rtasidagi va nomlangan volume bilan bind mount
   o’rtasidagi farq nima?
2. Qaysi flag portni chiqaradi va host hamda konteyner portlari qaysi
   tartibda yoziladi?
3. Nega user tomonidan yaratilgan tarmoqdagi konteynerlar bir-birini nom
   bo’yicha topadi, sukut bo’yicha bridge’dagilar esa topmaydi?
