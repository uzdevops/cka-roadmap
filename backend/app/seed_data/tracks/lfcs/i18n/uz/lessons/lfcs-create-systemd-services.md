## Unit fayl yozish

Imtihon maqsadi - "create systemd services": berilgan dasturdan boot
paytida ishga tushadigan, nosozlikda qayta ishga tushadigan va journal’ga
log yozadigan boshqariladigan service yasash.

```bash
sudo vi /etc/systemd/system/myapp.service
```

```ini
[Unit]
Description=My application API
Documentation=https://example.com/docs
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
Environment="LOG_LEVEL=info" "PORT=8080"
EnvironmentFile=-/etc/myapp/env
ExecStartPre=/opt/myapp/bin/migrate
ExecStart=/opt/myapp/bin/server --port ${PORT}
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
TimeoutStartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload            # unit yaratgach yoki tahrirlagach DOIM
sudo systemctl enable --now myapp
systemctl status myapp
journalctl -u myapp -f
```

## Uchta seksiya

**`[Unit]`** - identifikatsiya va tartib. `Description` `status` chiqishida
va loglarda ko’rinadi. `After=`/`Before=` start tartibini belgilaydi, lekin
talab **yaratmaydi**; `Wants=` - yumshoq bog’liqlik (uni ham ishga
tushiring, lekin u ishlamasa, davom eting); `Requires=` - qattiq (u
ishlamasa, biz ham ishlamaymiz). Ishlaydigan network talab qiladigan har
qanday narsa uchun `After=network-online.target` **va**
`Wants=network-online.target` birga - yolg’iz `network.target` faqat
"network stack ko’tarilgan" degani, "manzil sozlangan" degani emas.

**`[Service]`** - uni qanday ishga tushirish.

| Direktiva | Ma’nosi |
|---|---|
| `Type=simple` | sukut bo’yicha: `ExecStart` **aynan** daemon va fork qilmaydi |
| `Type=forking` | dastur fork qiladi va ota-jarayon chiqadi (eski uslubdagi daemon’lar); odatda `PIDFile=` bilan |
| `Type=oneshot` | ishlaydi va chiqadi; sozlash topshiriqlari uchun `RemainAfterExit=yes` bilan juftlang |
| `Type=notify` | dastur systemd’ga qachon tayyor bo’lganini aytadi (sd_notify) |
| `ExecStart=` | buyruq - **absolut yo’l**, shell sintaksisi yo’q (`/bin/bash -c '…'` ishlatmasangiz, pipe ham, `&&` ham yo’q) |
| `ExecStartPre=` / `ExecStartPost=` | oldin / keyin; ishlamagan `Pre` start’ni to’xtatadi (nosozlikni e’tiborsiz qoldirish uchun `-` prefiksi) |
| `ExecReload=` | `systemctl reload` nimani ishga tushiradi |
| `ExecStop=` | odatda kerak emas - systemd SIGTERM yuboradi |
| `User=` / `Group=` | imtiyozsiz ishga tushiring - shuni qiling |
| `WorkingDirectory=` | mavjud bo’lishi shart |
| `Environment=` / `EnvironmentFile=` | o’zgaruvchilar (`-` prefiksi = ixtiyoriy fayl) |
| `Restart=` | `no` (sukut bo’yicha), `on-failure`, `always`, `on-abnormal` |
| `RestartSec=` | qayta ishga tushirishdan oldin kutish |
| `TimeoutStartSec=` / `TimeoutStopSec=` | systemd qancha kutadi |
| `StandardOutput=` / `StandardError=` | `journal` (sukut bo’yicha), `null`, `append:/var/log/x.log` |
| `PIDFile=` | `Type=forking` uchun |

**`[Install]`** - `enable` nima qilishi. Oddiy service uchun javob -
`WantedBy=multi-user.target`; `[Install]` seksiyasisiz `enable` "no
installation config" bilan ishlamaydi.

## Bir martalik texnik xizmat unit’i

```ini
# /etc/systemd/system/cleanup.service
[Unit]
Description=Clean old temporary files

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cleanup.sh
```

Talab bo’yicha (`systemctl start cleanup`) yoki timer bilan jadval asosida
(6-hafta) ishga tushiring. Uni faqat timer ishga tushirsa, `[Install]`
kerak emas.

## Hardening, arzoniga

```ini
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict          # / bu service uchun faqat o'qish uchun
ProtectHome=yes
ReadWritePaths=/var/lib/myapp
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
LimitNOFILE=65535
MemoryMax=512M
```

Buzib kirilgan service’ni ancha kichik muammoga aylantiradigan besh satr.
`systemd-analyze security myapp` unit’ga ball qo’yadi va nima
yetishmayotganini sanab beradi.

## Unit’ga ishonishdan oldin uni sinash

```bash
systemd-analyze verify /etc/systemd/system/myapp.service     # sintaksis va havolalar
sudo systemctl daemon-reload
sudo systemctl start myapp && systemctl status myapp
sudo systemctl stop myapp; sudo systemctl restart myapp
journalctl -u myapp -n 30 --no-pager
sudo systemctl enable myapp && systemctl is-enabled myapp
sudo reboot                                                   # haqiqiy sinov, imkoningiz bo'lsa
```

## Template unit’lar, qisqacha

`worker@.service` nomli unit - template; `%i` - instance nomi:

```ini
# /etc/systemd/system/worker@.service
[Service]
ExecStart=/opt/app/worker --queue %i
```

```bash
sudo systemctl enable --now worker@images.service worker@email.service
```

Bitta fayl, ko’plab instance’lar - `getty@tty1` va `sshd@` shunday ishlaydi.

:::warning
`ExecStart=` shell buyruq satri **emas**: `ExecStart=/usr/bin/foo > /var/log/foo.log`
yo’naltirmaydi, u `>`’ni argument sifatida uzatadi.
`StandardOutput=append:/var/log/foo.log` yoki
`ExecStart=/bin/bash -c '/usr/bin/foo > /var/log/foo.log'` ishlating. Xuddi
shu narsa `&&`, `|`, `*` va systemd’ning o’z `${VAR}` idan tashqaridagi
`$VAR` ochilishiga ham tegishli.
:::

:::exam-tip
Kutiladigani: "X nomli service yarating, u boot paytida Y user nomidan
/path/to/script ni ishga tushirsin va nosozlikda qayta ishga tushsin".
Uchta seksiyani yozing, `daemon-reload`, `enable --now`, keyin buni
`systemctl is-active X`, `is-enabled X` va `journalctl -u X` bilan
isbotlang. Ball yo’qotadigan ikki xato - yetishmayotgan
`[Install] WantedBy=` (shunda `enable` ishlamaydi) va unutilgan
`daemon-reload`.
:::

## O’zingizni tekshiring

1. Unit faylning uchta seksiyasi qaysilar va har biri nima qiladi?
2. `Type=simple`, `Type=forking` va `Type=oneshot` orasidagi farq nima?
3. `ExecStart=/usr/bin/foo > /tmp/out` nega ko’rinib turganidek
   ishlamaydi?
