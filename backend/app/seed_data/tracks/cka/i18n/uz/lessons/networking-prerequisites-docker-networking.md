## Docker taklif qiladigan uchta tarmoq

```bash
docker run --network none nginx      # faqat loopback'li namespace - tarmoq umuman yo'q
docker run --network host nginx      # alohida namespace YO'Q: host stegini baham ko'radi, host'ning 80-portini to'g'ridan-to'g'ri band qiladi
docker run nginx                     # sukut bo'yicha: bridge
```

| Rejim | Namespace | Yetib borish |
|---|---|---|
| `none` | o’ziniki, bo’sh | na ichkariga, na tashqariga |
| `host` | host’niki | host’da bor hamma narsa; host bilan port to’qnashuvi |
| `bridge` | o’ziniki, `docker0`’ga ulangan | bridge’dagi boshqa konteynerlar va NAT orqali tashqarisi |

Kubernetes’da xuddi shu ikki chekka Pod maydonlari sifatida bor:
`hostNetwork: true` - bu `--network host` (ba’zi CNI va monitoring
DaemonSet’lari ishlatadi), CNI sozlanmagan Pod esa amalda `none`
(`ContainerCreating`’da qotib qoladi).

## Bridge tarmog’i - o’tgan darsdagi sxemaning o’zi

```bash
ip link                     # docker0 - bridge, 172.17.0.1/16, Docker ishga tushganda yaratilgan
docker run -d --name web nginx
docker inspect web --format '{{.NetworkSettings.IPAddress}}'   # 172.17.0.2
ip link                     # yangi vethXXXX paydo bo'ldi, master docker0
ip netns                    # Docker o'z namespace'larini yashiradi; quyiga qarang
```

Docker siz uchun quyidagilarni qildi: network namespace yaratdi, veth
juftligini yaratdi, uning bir uchini namespace ichiga 172.17.0.2/16 manzilli
`eth0` sifatida qo’ydi, ikkinchi uchini `docker0`’ga uladi, namespace ichida
172.17.0.1 orqali default route qo’shdi va - birinchi ishga tushishda -
konteyner internetga chiqa olishi uchun 172.17.0.0/16 ga iptables MASQUERADE
qoidasini qo’shdi.

```bash
# namespace'ni ip netns bilan ko'rish uchun uni kutilgan joyga bog'lang
pid=$(docker inspect web --format '{{.State.Pid}}')
mkdir -p /var/run/netns && ln -s /proc/$pid/ns/net /var/run/netns/web
ip netns exec web ip addr            # eth0 172.17.0.2
ip netns exec web ip route           # default via 172.17.0.1
```

## Port mapping

Bridge’dagi konteynerning shaxsiy manzili bo’ladi va unga host tashqarisidan
hech kim yeta olmaydi. `-p` uni ochib beradi:

```bash
docker run -d -p 8080:80 nginx
curl http://<host-ip>:8080              # host'ga yeta oladigan har qanday joydan
iptables -t nat -L DOCKER -n | grep 8080
# DNAT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80
```

Bu - iptables **DNAT** qoidasi: host’ning 8080-portiga kelgan trafik
konteynerning IP’si va portiga qayta yoziladi. Aynan shu bitta qoida -
NodePort Service ortidagi g’oya: node portiga kelgan trafikni uning ortidagi
Pod’ga qayta yozish - kube-proxy esa har bir node’da har bir Service uchun
shu qoidalarni yozadigan dastur.

## Kubernetes qayerda ajralib ketadi

Docker’ning bridge’i har bir host uchun alohida: har bir hostda o’zining
172.17.0.0/16 i bor va turli hostlardagi konteynerlar port mapping’siz
bir-biriga yeta olmaydi. Kubernetes esa klasterdagi har bir Pod boshqa har
qanday Pod’ga node’lar osha, NAT’siz, **o’z Pod IP’si bo’yicha** yeta
olishini talab qiladi. CNI plugin Docker bitta hostda qilgan ishdan tashqari
aynan shuni qiladi: har bir node’ga alohida Pod subnet’ini beradi va har bir
node boshqa har bir node’ning subnet’iga marshrut qila olishini ta’minlaydi
(route’lar bilan yoki overlay bilan). Keyingi dars.

:::tip
`docker network ls` `bridge`, `host`, `none` va foydalanuvchi yaratgan har
qanday tarmoqlarni ko’rsatadi. Foydalanuvchi yaratgan bridge tarmoqlari
konteynerlar orasiga nom bo’yicha DNS qo’shadi - bu CoreDNS Pod’lar uchun
qiladigan ishning kichik ko’rinishi.
:::

## O’zingizni tekshiring

1. `--network host` konteynerning namespace’ida nimani o’zgartiradi va uning
   Kubernetes’dagi ekvivalenti nima?
2. Docker konteynerni bridge’ga qo’yish uchun qiladigan beshta ishni sanang.
3. `-p 8080:80` qanday iptables qoidasini yaratadi va Kubernetes’ning qaysi
   obyekti xuddi shu ishni qiladi?
