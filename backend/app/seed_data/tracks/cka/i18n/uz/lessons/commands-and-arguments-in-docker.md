## Jarayoni to’xtaganda konteyner nega to’xtaydi

Konteyner - VM emas. U "boot" bo’lib, tik turavermaydi - u **bitta
jarayonni** ishga tushiradi va o’sha jarayon tugaganda konteyner ham tugaydi.
`docker run ubuntu` ni ishga tushiring - u darhol to’xtaydi, chunki
Ubuntu’ning sukut bo’yicha buyrug’i - `bash`, bash esa ulangan terminal
topmaydi va chiqib ketadi. Shuning uchun har bir image o’z jarayoni nima
ekanini aytishi kerak.

```dockerfile
FROM ubuntu
CMD sleep 5
```

```bash
docker build -t ubuntu-sleeper .
docker run ubuntu-sleeper            # 5 soniya uxlaydi va chiqadi
docker run ubuntu-sleeper sleep 10   # argument CMD'ni butunlay ALMASHTIRADI
```

## CMD va ENTRYPOINT

Nima ishga tushishini ikkita direktiv hal qiladi; farq - buyruq qatorida
uzatgan argumentlaringizga nima bo’lishida.

| Direktiv | `docker run image` da | `docker run image X` da |
|---|---|---|
| `CMD ["sleep", "5"]` | `sleep 5` ishlaydi | `X` ishlaydi - **CMD almashtiriladi** |
| `ENTRYPOINT ["sleep"]` | `sleep` ishlaydi (va argumentsiz xato beradi) | `sleep X` ishlaydi - **X oxiriga qo’shiladi** |
| `ENTRYPOINT ["sleep"]` + `CMD ["5"]` | `sleep 5` ishlaydi | `sleep X` ishlaydi - CMD *sukut bo’yicha* argument |

```dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
CMD ["5"]
```

```bash
docker run ubuntu-sleeper         # sleep 5
docker run ubuntu-sleeper 10      # sleep 10
docker run --entrypoint sleep2.0 ubuntu-sleeper 10    # sleep2.0 10 - ENTRYPOINT'ning o'zini bekor qilish
```

O’sha andaza - `ENTRYPOINT` dastur, `CMD` esa uning sukut bo’yicha
argumentlari - yaxshi qurilgan image’larning ko’pi ishlatadigan andaza va
Kubernetes’ning ikkita maydoni aynan shunga moslashadi.

## Shell form va exec form

```dockerfile
CMD sleep 5                  # shell form: aslida  /bin/sh -c "sleep 5"  ishlaydi
CMD ["sleep", "5"]           # exec form: to'g'ridan-to'g'ri  sleep 5  ishlaydi
```

Sizga kerak bo’lgani - exec form (JSON massiv): jarayon PID 1 bo’ladi,
signallarni oladi (shu sababli `docker stop` va Kubernetes’ning SIGTERM’i
unga yetib boradi) va image’da shell bo’lishi shart emas. Shell form buyruqni
`sh -c` ichiga o’raydi, bu esa signallarni yutadi va toza to’xtashni
ishonchsiz qiladi.

:::warning
`ENTRYPOINT ["sleep", "5"]` va `ENTRYPOINT sleep 5` - bir xil narsa emas.
Shell form `CMD` ni ham, qo’shilgan argumentlarni ham butunlay e’tiborsiz
qoldiradi, chunki `sh -c "sleep 5"` allaqachon to’liq buyruq. Agar
argumentlar "hech narsa qilmayotgan" bo’lsa, Dockerfile qaysi formni
ishlatganini tekshiring.
:::

## Image nimani ishga tushirishini ko’rish

```bash
docker inspect ubuntu-sleeper --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'
# [sleep] [5]
crictl inspecti nginx:1.27 | grep -A3 -i entrypoint     # docker siz Kubernetes node ida
```

Kubernetes topshirig’i sizga image berib, uni "--color=green argumenti bilan
ishga tushiring" desa, `--color=green` ENTRYPOINT’ga argumentmi (u holda
`args` ga tushadi) yoki butun buyruqmi (u holda `command` ga tushadi) - buni
mana shunday aniqlaysiz. Keyingi dars bu moslikni aniq qilib beradi.

## O’zingizni tekshiring

1. Image’da `CMD ["sleep", "5"]` bor. `docker run image sleep 10` uchun nima
   ishlaydi va nega?
2. Image’da `ENTRYPOINT ["sleep"]` va `CMD ["5"]` bor. `docker run image 10`
   uchun-chi, `docker run image` uchun-chi, nima ishlaydi?
3. Toza to’xtashi kerak bo’lgan konteyner uchun nega `CMD ["nginx", "-g",
   "daemon off;"]` `CMD nginx -g "daemon off;"` dan yaxshiroq?
