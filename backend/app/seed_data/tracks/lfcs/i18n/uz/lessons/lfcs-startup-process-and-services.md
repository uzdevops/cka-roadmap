## Hamma narsani systemd ishga tushiradi

PID 1 - bu `systemd`; qolgan hamma narsa u boshqaradigan **unit**.
Uchraydigan unit turlari: `.service` (daemon), `.socket`, `.timer`
(6-hafta), `.mount`, `.target` (o’tgan dars), `.path`, `.device`.

```bash
systemctl status nginx
# ● nginx.service - A high performance web server
#      Loaded: loaded (/lib/systemd/system/nginx.service; enabled; preset: enabled)
#      Active: active (running) since Wed 2026-08-19 09:12:01 UTC; 2h ago
#    Main PID: 1234 (nginx)
#       Tasks: 3 (limit: 4657)
#      Memory: 12.4M
#         CGroup: /system.slice/nginx.service
#                 ├─1234 nginx: master process
#                 └─1235 nginx: worker process
# Aug 19 09:12:01 web01 systemd[1]: Started A high performance web server.
```

Ma’noning katta qismini ikkita so’z tashiydi: **Loaded: … enabled** (boot
paytida ishga tushadimi?) va **Active: active (running)** (hozir
ishlayaptimi?). Ular bir-biridan mustaqil - service hozir ishlab, boot
paytida ishga tushmasligi mumkin, yoki aksincha.

## Fe’llar

```bash
sudo systemctl start nginx            # hozir
sudo systemctl stop nginx
sudo systemctl restart nginx          # to'xtatadi, keyin ishga tushiradi
sudo systemctl reload nginx           # ulanishlarni uzmasdan configni qayta o'qish (qo'llab-quvvatlansa)
sudo systemctl reload-or-restart nginx
sudo systemctl enable nginx           # boot paytida
sudo systemctl disable nginx
sudo systemctl enable --now nginx     # ikkalasi ham, bitta buyruqda
sudo systemctl disable --now nginx
sudo systemctl mask nginx             # umuman ishga tushirib bo'lmaydi, hatto bog'liqlik sifatida ham
sudo systemctl unmask nginx
systemctl is-active nginx; systemctl is-enabled nginx; systemctl is-failed nginx
```

`enable` target’ning `.wants` direktoriyasidan unit faylga **symlink**
yaratadi - shuning uchun ham "enabled" holati filesystem’da ko’rinadi:

```bash
ls -l /etc/systemd/system/multi-user.target.wants/
```

## Atrofga nazar tashlash

```bash
systemctl                                    # har bir aktiv unit
systemctl list-units --type=service          # faqat service'lar
systemctl list-units --type=service --state=running
systemctl --failed                           # nima buzilgan - notanish tizimdagi birinchi buyruq
systemctl list-unit-files --type=service     # har bir O'RNATILGAN unit va uning enabled/disabled holati
systemctl list-unit-files --state=enabled
systemctl cat nginx                          # unit fayl(lar)i, drop-in'lar bilan birga
systemctl show nginx -p ExecStart -p Restart # alohida xossalar
systemctl list-dependencies nginx            # unga nima kerak
systemctl list-dependencies --reverse nginx  # u kimga kerak
systemd-analyze verify /etc/systemd/system/my.service    # sintaksisni tekshirish
```

## Unit fayllar qayerda turadi

| Yo’l | Nima | Ustunlik |
|---|---|---|
| `/lib/systemd/system/` (yoki `/usr/lib/systemd/system/`) | paketlar bilan keladi | eng past |
| `/run/systemd/system/` | runtime, vaqtinchalik | o’rtada |
| `/etc/systemd/system/` | **sizniki** - lokal unit’lar va override’lar | **eng yuqori** |

`/lib` dagi paket unit’ini hech qachon tahrirlamang - paket yangilanishi
uni qayta yozib yuboradi. Buning o’rniga override qiling:

```bash
sudo systemctl edit nginx            # /etc/systemd/system/nginx.service.d/override.conf ni yaratadi
# [Service]
# Restart=always
# RestartSec=5
sudo systemctl edit --full nginx     # tahrirlash uchun butun unit'ni /etc ga nusxalaydi
sudo systemctl daemon-reload         # unit fayllarni qo'lda o'zgartirgach DOIM
sudo systemctl restart nginx
systemctl cat nginx                  # endi nima kuchda ekanini tasdiqlang
```

`systemctl edit` `daemon-reload` ni siz uchun bajaradi; faylni qo’lda
tahrirlash esa bajarmaydi - va unutilgan `daemon-reload` systemd eski
ta’rifni ishlatishda davom etadi degani, bu esa besh daqiqalik chalkashlik.

## Nosozlikni o’qish

```bash
systemctl status myapp
# Active: failed (Result: exit-code) since ...; 10s ago
# Process: 4321 ExecStart=/usr/local/bin/myapp (code=exited, status=203/EXEC)
journalctl -u myapp -n 50 --no-pager
journalctl -u myapp -f
journalctl -u myapp -b -p err
journalctl -xeu myapp                 # systemd tavsiya qiladigan kombinatsiya: izohlar, oxiri, shu unit
```

| status= | Odatda |
|---|---|
| `203/EXEC` | `ExecStart` dagi binary mavjud emas yoki bajariladigan emas |
| `200/CHDIR` | `WorkingDirectory` mavjud emas |
| `217/USER` | `User=` da ko’rsatilgan user mavjud emas |
| `1` | dasturning o’zi ishlamadi - uning o’z log satrlarini o’qing |
| `226/NAMESPACE` | sandbox direktivasi (`ProtectSystem`, `PrivateTmp`) nimanidir to’sib qo’ygan |
| `timeout` | service tayyorligini bildirmadi - `Type=` noto’g’ri |

## Bog’liqliklar, qisqacha

`After=`/`Before=` tartibni belgilaydi; `Requires=`/`Wants=` ehtiyojni
belgilaydi (`Wants` - yumshog’i: xohlangan unit ishlamasa ham, unit
baribir ishga tushadi). Unit boot paytida ishga tushadi, chunki uni biror
**target** xohlaydi - buni `enable` `[Install]` ichidagi `WantedBy=`
orqali tashkil qiladi.

```bash
systemctl list-dependencies multi-user.target | grep nginx
systemctl show nginx -p After -p Wants -p WantedBy
```

:::exam-tip
Topshiriq matni bir-biriga aynan mos keladi: "X boot paytida ishga tushsin
va uni hozir ham ishga tushiring" → `systemctl enable --now X`; "uni
to’xtating va umuman ishga tushmasligini ta’minlang" → `systemctl mask X`
(yoki `disable --now`); "nega ishlamadi" → `systemctl status X`, keyin
`journalctl -u X`. Har bir o’zgarishni `systemctl is-active` **va**
`is-enabled` bilan tekshiring - topshiriqlar odatda ikkalasini ham
tekshiradi.
:::

## O’zingizni tekshiring

1. `start` va `enable` orasidagi, `disable` va `mask` orasidagi farq
   nima?
2. Sizning o’z unit fayllaringiz va override’laringiz qayerda turishi
   kerak va ulardan birini qo’lda tahrirlagandan keyin nimani ishga
   tushirishingiz shart?
3. Service `status=203/EXEC` bilan ishlamadi. Nimasi noto’g’ri?
