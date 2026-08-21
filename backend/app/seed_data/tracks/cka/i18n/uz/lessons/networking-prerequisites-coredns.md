## DNS serverni qo’lda ishga tushirish

CoreDNS bilan `kube-system`’dagi Deployment sifatida uchrashishdan oldin,
uni bir marta oddiy binar sifatida ishga tushiring - shunda keyinroq
tahrirlaydigan ConfigMap’ingiz "shunchaki Corefile" ekani ravshan bo’ladi.

```bash
wget https://github.com/coredns/coredns/releases/download/v1.11.1/coredns_1.11.1_linux_amd64.tgz
tar -xzf coredns_1.11.1_linux_amd64.tgz
./coredns                      # konfigsiz :53 ni tinglaydi - foydali hech nima javob bermaydi
```

## Corefile

CoreDNS bitta fayl bilan sozlanadi: bu **server blok**lar ro’yxati, har
biri bitta zona va **plugin**lar zanjiri:

```
# Corefile
. {
    hosts /etc/hosts {        # answer from a hosts-format file
        fallthrough           # ...and if the name is not there, continue to the next plugin
    }
    forward . 8.8.8.8         # everything else: ask Google
    log
    errors
}
```

```bash
./coredns -conf Corefile
dig @localhost web            # /etc/hosts dan javob berildi
dig @localhost example.com    # 8.8.8.8 ga uzatildi
```

Server blokni pipeline sifatida o’qing: `.` zonasidagi (ya’ni hamma
narsadagi) nom uchun so’rov `hosts`’dan o’tadi, u javob bera olsa javob
beradi, aks holda `forward`’ga tushib ketadi. `log` va `errors` - kuzatuv
plugin’lari. Shu shakl - zona, plugin’lar zanjiri va ulardan biri javob
beradi - butun modelning o’zi.

## Kubernetes bilan keladigan Corefile

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

```
.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

| Plugin | Nima qiladi |
|---|---|
| `kubernetes cluster.local ...` | **asosiy** plugin: API orqali Service va Pod’larni kuzatadi va `*.cluster.local`’ga javob beradi |
| `forward . /etc/resolv.conf` | `cluster.local` bo’lmagan hamma narsa node’ning upstream resolver’lariga ketadi |
| `cache 30` | javoblarni 30 s keshlaydi |
| `health`, `ready` | Deployment ishlatadigan probe’lar |
| `reload` | ConfigMap o’zgarganda Corefile’ni qayta o’qiydi (restart shart emas) |
| `loop` | uzatish tsiklini (CoreDNS o’zini o’ziga uzatishini) aniqlaydi va aylanib qolish o’rniga baland ovozda qulaydi |

"CoreDNS nega X ni shunday aniqlaydi" degan har qanday savolga shu
qatorlardan biri javob beradi. ConfigMap’ni o’zgartiring - `reload` uni
bir-ikki daqiqada oladi.

## Amalda qilishingiz mumkin bo’lgan ikki tahrir

**Shaxsiy domenni o’z DNS’ingizga uzatish:**

```
corp.internal:53 {
    errors
    cache 30
    forward . 10.10.0.53
}
```

Uni ConfigMap’ga ikkinchi server blok sifatida qo’shing; endi har qanday
Pod’dan `*.corp.internal` korporativ resolver’ga ketadi.

**Nomni qayta yozish** (`rewrite` plugin’i): `rewrite name old.example.com
new.example.com` - ilovaga hostname qattiq yozib qo’yilgan bo’lsa, ba’zan
eng tez yechim.

:::exam-tip
`forward . /etc/resolv.conf` qatori - Pod nega `google.com`’ni aniqlay
olishining sababi: CoreDNS **node** nimadan foydalansa, o’shandan so’raydi.
Pod’lardan tashqi nomlar ishlamay, klaster nomlari ishlasa, node’larning
`/etc/resolv.conf` faylini tekshiring - va CoreDNS loglaridagi `loop`
plugin’ini: node resolver’i CoreDNS’ga qaytib ko’rsatganda u muammoni
aniq nomlab beradi.
:::

## O’zingizni tekshiring

1. Server blok nima va uning ichida `fallthrough` nima qiladi?
2. `api.payroll.svc.cluster.local`’ga qaysi plugin javob beradi,
   `example.com`’ga qaysi biri?
3. coredns ConfigMap’idagi o’zgarish ishlayotgan CoreDNS Pod’lariga qanday
   yetib boradi?
