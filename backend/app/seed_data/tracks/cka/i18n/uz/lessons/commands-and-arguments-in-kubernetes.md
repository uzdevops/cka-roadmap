## Moslik

| Dockerfile | Pod spec maydoni | Ma’nosi |
|---|---|---|
| `ENTRYPOINT` | `command` | bajariladigan fayl |
| `CMD` | `args` | uning argumentlari |

Nomlanish - tuzoq: Kubernetes’dagi `command` Docker’dagi **ENTRYPOINT**’ni
almashtiradi, CMD’ni emas; Kubernetes’dagi `args` esa Docker’dagi **CMD**’ni
almashtiradi. Bu boshingizga o’rnashgandan keyin qolgani mexanik ish.

`ENTRYPOINT ["sleep"]` va `CMD ["5"]` bilan qurilgan image uchun:

```yaml
# sleep 5  - hech narsa almashtirilmagan
spec:
  containers:
    - name: s
      image: ubuntu-sleeper

# sleep 10 - args CMD'ni almashtiradi, ENTRYPOINT saqlanadi
      args: ["10"]

# sleep2.0 10 - command ENTRYPOINT'ni almashtiradi; args baribir kerak, chunki...
      command: ["sleep2.0"]
      args: ["10"]
```

:::warning
Agar `command`ni belgilab, `args`ni **belgilamasangiz**, image’ning CMD’si
saqlanmaydi, balki **tashlab yuboriladi**. Yolg’iz `command: ["sleep2.0"]`
`sleep2.0`ni hech qanday argumentsiz ishga tushiradi. To’rt holat:

| `command` | `args` | nima ishga tushadi |
|---|---|---|
| – | – | image’dagi ENTRYPOINT + CMD |
| – | belgilangan | ENTRYPOINT + sizning args |
| belgilangan | – | sizning command, argumentlar **yo’q** |
| belgilangan | belgilangan | sizning command + sizning args |
:::

## Uni xatosiz yozish

Ikkala maydon ham satrlar ro’yxati. Bir xil natija beradigan ikki uslub:

```yaml
command: ["sleep", "5000"]
# yoki
command:
  - sleep
  - "5000"
```

`"5000"` atrofidagi qo’shtirnoqlar muhim: aks holda YAML `5000`ni son deb
o’qiydi, maydon esa satr talab qiladi. Flow ro’yxati ichida chiziqcha bilan
boshlanadigan `"--color=green"` kabi flaglar uchun ham shunday - baribir
qo’shtirnoqqa oling va bu haqda o’ylashni bas qiling.

```bash
# uni generatsiya qilish - eng tez va to'g'ri yo'l
kubectl run ubuntu-sleeper-2 --image=ubuntu --command -- sleep 5000 $do
#   -> command: [sleep, "5000"]   (-- dan keyingi hammasi command bo'ladi)
kubectl run webapp-green --image=kodekloud/webapp-color -- --color=green $do
#   -> args: [--color=green]       (--command flagisiz bu args bo'ladi)
```

O’sha `--command` flagi - butun farq shu: u bilan `--` dan keyingi narsa
`command` bo’ladi; usiz esa `args`.

## Ishlab turgan Pod’ga nima berilganini o’qish

```bash
kubectl get pod ubuntu-sleeper -o jsonpath='{.spec.containers[0].command}'
kubectl get pod ubuntu-sleeper -o jsonpath='{.spec.containers[0].args}'
kubectl describe pod ubuntu-sleeper | grep -A4 "Command:\|Args:"
```

Agar ikkala maydon ham belgilanmagan bo’lsa, `kubectl` hech narsa
ko’rsatmaydi - jarayon image’dan keladi va uni node’da `crictl inspecti
<image>` (yoki boshqa joyda `docker inspect`) orqali o’qiysiz.

:::exam-tip
"Pod `sleep 5000` buyrug’ini ishga tushirsin" degan topshiriqda
`command: ["sleep", "5000"]` kerak (hamma narsa almashtiriladi). "Image’ga
`--color=green` argumentini uzating" degan topshiriqda esa
`args: ["--color=green"]` kerak (ENTRYPOINT saqlanadi). Ikki fe’l, ikki
maydon. Va yodda tuting: ishlab turgan Pod’da bu maydonlar o’zgarmas -
o’chirib qayta yaratiladi.
:::

## Kerak bo’lganda shell

Ba’zan buyruq haqiqatan ham shell one-liner bo’ladi:

```yaml
command: ["/bin/sh", "-c"]
args: ["echo starting; exec myapp --port 8080"]
```

Oxiridagi `exec` `myapp`ni PID 1 sifatida shell o’rniga qo’yadi, shunda
signallar unga yetib boradi. `exec`siz SIGTERM `sh`ga boradi, u esa uni
uzatmaydi va konteyner o’ldirilishini kutib turadi.

## O’zingizni tekshiring

1. Qaysi Pod maydoni Dockerfile’dagi `ENTRYPOINT`ni almashtiradi va qaysisi
   `CMD`ni?
2. Image sukut bo’yicha `sleep 5` ishga tushiradi. Siz faqat
   `command: ["sleep"]` deb qo’ydingiz. Nima ishga tushadi?
3. `busybox` image’idan `sleep 3600` ishlatadigan Pod yaratadigan `kubectl
   run` buyrug’ini yozing, va image’ning o’z entrypoint’iga `--verbose`
   argumentini uzatadigan variantini ham.
