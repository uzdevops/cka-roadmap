## Konteyner - hostdagi jarayon

Kubernetes’ning security context’lari mantiqiy ko’rinishidan oldin bitta
faktni aniq bilib olishingiz kerak: konteyner - virtual mashina emas. U host
kernelidagi jarayon (yoki bir nechta jarayon) bo’lib, **namespace**’lar bilan
o’ralgan (shuning uchun u o’zining PID’larini, tarmog’ini, mount’larini,
hostname’ini ko’radi) va **cgroup**’lar bilan chegaralangan (shuning uchun
uning CPU va xotirasi cheklangan). Kernel umumiy. Izolyatsiya - kernel
majburlagan narsadan iborat, undan ortig’i emas.

```bash
docker run -d --name sleeper ubuntu sleep 3600
ps -ef | grep "sleep 3600"             # HOST'da: o'sha jarayon, ko'rinib turadi, PID 4023
docker exec sleeper ps -ef             # ichkarida: u PID 1
```

Bitta jarayon, ikki xil ko’rinish. Bu shuni anglatadi: jarayon qaysi
foydalanuvchi sifatida ishlashi va qanday imtiyozlarga ega bo’lishi -
**host** haqidagi savollar.

## Foydalanuvchilar

Sukut bo’yicha konteyner jarayoni **root** (UID 0) sifatida ishlaydi -
konteyner ichida root *va* hostda UID 0. Zararni ikki narsa cheklaydi:

1. Image foydalanuvchini tanlashi mumkin: Dockerfile’da `USER 1000` yoki ishga
   tushirish paytida `--user`.

```bash
docker run --user=1000 ubuntu sleep 3600
ps -ef | grep "sleep 3600"       # 1000  ...  sleep 3600
```

2. Hatto root bo’lganda ham, konteyner jarayoni root’ning barcha
   vakolatlarini olmaydi. Linux root’ni **capability**’larga ajratadi va
   Docker konteynerga faqat kichik sukut bo’yicha to’plamni beradi.

## Capabilities

```bash
# sukut bo'yicha konteyner buni qila olmaydi:
docker run ubuntu date -s "1 JAN 2030"        # clock_settime: Operation not permitted  (SYS_TIME kerak)
docker run ubuntu reboot                      # SYS_BOOT kerak
```

| Capability | Jarayonga nima imkon beradi |
|---|---|
| `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETUID`, `SETGID`, `NET_BIND_SERVICE`, `KILL`, ... | sukut bo’yicha to’plam - web serverni root sifatida ishlatishga yetarli |
| `SYS_TIME` | soatni o’rnatish |
| `NET_ADMIN` | interfeyslarni, marshrutlarni, iptables’ni o’zgartirish |
| `SYS_ADMIN` | mount va namespace amallarining aralash to’plami - deyarli root |
| `SYS_PTRACE` | boshqa jarayonlarni kuzatish |

```bash
docker run --cap-add SYS_TIME ubuntu date -s "1 JAN 2030"    # ishlaydi
docker run --cap-drop KILL ubuntu ...                         # bittasini olib tashlash
docker run --privileged ubuntu ...                            # BARCHA capability lar + qurilmalarga kirish: nomidan boshqa hammasi bo'yicha hostdagi root shell
```

`--privileged` - CNI yoki storage plagin’iga ba’zan kerak bo’ladigan va hech
bir ilovada bo’lmasligi kerak bo’lgan narsa. Kubernetes aynan shu
tugmachalarni - `runAsUser`, `capabilities.add/drop`, `privileged` -
`securityContext` ostida beradi, bu esa keyingi dars.

## Bilishga arzigulik boshqa sukut bo’yicha holatlar

- Root fayl tizimi yoziladigan; `--read-only` uni yozib bo’lmaydigan qiladi.
- Fayl tizimiga kirish konteynerning o’z qatlamlari va siz mount qilgan
  narsalar bilan cheklangan; hostning `/` katalogini yoki Docker soketini
  mount qilish - qochish yo’li.
- Host tarmog’i yo’q (`--network host` buni o’zgartiradi), host PID
  namespace’i yo’q (`--pid host` buni o’zgartiradi). Kubernetes’da xuddi shu
  ikkitasi uchun `hostNetwork` va `hostPID` bor.
- **seccomp** profili qaysi syscall’larga ruxsat berilishini filtrlaydi;
  **AppArmor** yoki **SELinux** jarayon qaysi fayllar va capability’larga
  tegishi mumkinligini belgilaydi. Ikkalasi ham CKS hududi; CKA’ga faqat
  foydalanuvchi/capability/privileged uchligi kerak.

:::tip
Keyinchalik ham asqotadigan fikrlash modeli: *konteynerdagi root - bu hostdagi
root, capability’lari ayrilgan holda.* Har bir Kubernetes xavfsizlik sozlamasi
ulardan kamrog’ini qaytarib berish yoki umuman root bo’lmagan holda ishlash
haqida.
:::

## O’zingizni tekshiring

1. Konteynerning PID 1 i hostda ko’rinadimi? Qanday ko’rinishda?
2. Root sifatida ishlayotgan konteyner tizim soatini o’rnatmoqchi bo’ldi va
   rad etildi. Nega va nima bunga ruxsat bergan bo’lardi?
3. `--privileged` nima beradi va u `--cap-add
   SYS_ADMIN`’dan nega farq qiladi?
