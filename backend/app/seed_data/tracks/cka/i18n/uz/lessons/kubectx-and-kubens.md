## Ikkita doimiy yumush uchun ikkita kichkina vosita

Klasterni almashtirish va namespace’ni almashtirish - siz eng ko’p
qiladigan va eng uzun buyruqlarni yozadigan ikki ish:

```bash
kubectl config use-context prod-cluster
kubectl config set-context --current --namespace=payroll
```

**kubectx** va **kubens** (bitta loyiha, github.com/ahmetb/kubectx) shularni
o’rab beradi:

```bash
kubectx                       # kontekstlar ro'yxati, joriysi ajratib ko'rsatiladi
kubectx prod-cluster          # almashtirish
kubectx -                     # oldingisiga qaytish
kubectx dev=dev-user@cluster1 # kontekst nomini o'zgartirish

kubens                        # joriy kontekstdagi namespace lar ro'yxati
kubens payroll                # sukut bo'yicha namespace ni o'rnatish
kubens -                      # orqaga
kubens -c                     # joriy namespace ni chiqarish
```

Ular `kubectl config` tahrirlaydigan o’sha kubeconfig’ni tahrirlaydi -
qo’shimcha holat yo’q, shuning uchun ularni sof `kubectl config` bilan
aralashtirib ishlatish mumkin.

## O’rnatish

```bash
# release binarlari
sudo git clone https://github.com/ahmetb/kubectx /opt/kubectx
sudo ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx
sudo ln -s /opt/kubectx/kubens /usr/local/bin/kubens
# yoki: brew install kubectx / apt install kubectx (ba'zi distributivlarda) / kubectl krew plagini (kubectl ctx, kubectl ns)
```

`fzf` o’rnatilgan bo’lsa, ular interaktiv tanlagichga aylanadi.

## Nega bu xavfsizlik bosqichida turibdi

Chunki "men qaysi klasterga yo’naltirilganman" - bu xavfsizlik savoli. Har
bir jamoa boshidan bir marta o’tkazgan hodisa: staging uchun mo’ljallangan
buzg’unchi buyruq productionda ishga tushdi, chunki shell hamon noto’g’ri
kontekstda edi. Buning oldini ikki odat oladi:

1. Kontekstni **ko’rinadigan** qiling - `kubectx -c` / `kubens -c` ni
   ko’rsatadigan prompt (kube-ps1 shuni qiladi) yoki hech bo’lmaganda har
   qanday buzg’unchi ishdan oldin `kubectx` ni ishga tushirish.
2. **Hisob ma’lumotlarini** boshqacha qiling - foydalanuvchisi sukut
   bo’yicha `view` ga ega production konteksti va o’zgarishlar uchun alohida
   kontekst. Shunda noto’g’ri oyna xavfsiz ishlamay qoladi.

:::tip
Imtihonda sizda kubectx bo’lmaydi; sizda `kubectl config use-context` va
qaysi kontekst kerakligini aytadigan topshiriq bo’ladi. Uni har bir
topshiriqning boshida, har safar yozing. U o’rnini bosayotgan odat esa
o’sha-o’sha: harakat qilishdan oldin qayerda ekaningizni biling.
:::

## Hech nima o’rnatmasdan ekvivalentlar

```bash
alias kctx='kubectl config use-context'
alias kns='kubectl config set-context --current --namespace'
kubectl config get-contexts          # ro'yxat
kubectl config current-context
kubectl config view --minify -o jsonpath='{..namespace}'     # joriy sukut bo'yicha namespace
```

## O’zingizni tekshiring

1. `kubectx` va `kubens` ni ishga tushirganingizda ular aslida nimani
   o’zgartiradi?
2. Nega joriy kontekstingizni bilish xavfsizlik masalasi?
3. `kubens payroll` ning kubectl’dagi ekvivalenti nima?
