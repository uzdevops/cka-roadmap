## Branch’lar: ishning parallel yo’nalishlari

Branch - commit’ga ishora qiluvchi ko’chma ko’rsatkich. Uni yaratish hech
narsaga turmaydi; almashish esa working tree’ni o’sha commit tarkibiga
o’tkazadi.

```bash
git branch                       # lokal branch'lar ro'yxati; * joriysini bildiradi
git branch -a                    # + remote-tracking branch'lar
git branch -vv                   # + oxirgi commit va har biri qaysi remote branch'ni kuzatishi
git branch feature-tls           # yaratish (almashtirmaydi)
git switch feature-tls           # almashish      [eskisi: git checkout feature-tls]
git switch -c feature-tls        # yaratish va almashish   [eskisi: git checkout -b]
git switch -                     # oldingi branch'ga qaytish
git branch -m old new            # nomini o'zgartirish
git branch -d feature-tls        # o'chirish (merge qilinmagan bo'lsa rad etadi)
git branch -D feature-tls        # baribir o'chirish
```

```
main      A───B───C───────F
                   \     /
feature-tls         D───E        (F - merge commit'i)
```

## Merge qilish

```bash
git switch main
git merge feature-tls            # branch commit'larini main'ga olib kirish
git merge --no-ff feature-tls    # har doim merge commit yaratish (branch tarixda ko'rinib turadi)
git merge --abort                # konfliktli merge'dan chiqish
git branch -d feature-tls        # merge'dan keyin tozalash
```

**Fast-forward**: agar main qimirlamagan bo’lsa, ko’rsatkich shunchaki
oldinga suriladi - merge commit yo’q. Aks holda Git ikkala tarixni
birlashtiruvchi commit yaratadi.

### Konfliktlar

Ikkala branch bir xil satrlarni o’zgartirgan bo’lsa, Git to’xtaydi va
faylni belgilab qo’yadi:

```
<<<<<<< HEAD
worker_connections 1024;
=======
worker_connections 4096;
>>>>>>> feature-tls
```

```bash
git status                       # "both modified: nginx.conf"
vi nginx.conf                    # kerakli natijaga keltiring, <<< === >>> belgilarini o'chiring
git add nginx.conf               # hal qilingan deb belgilash
git commit                       # merge'ni yakunlaydi (sukut bo'yicha xabar yetarli)
git merge --abort                # yoki: voz kechib, orqaga qaytish
```

Hech qanday sehr yo’q: to’g’ri tarkibni tanlang, belgilarni olib tashlang,
`add`, `commit`.

## Remote’lar

**Remote** - repozitoriyning boshqa nusxasiga berilgan nomli URL.

```bash
git remote -v
# origin  git@github.com:uzdevops/cka-roadmap.git (fetch)
# origin  git@github.com:uzdevops/cka-roadmap.git (push)
git remote add origin git@github.com:org/repo.git
git remote set-url origin https://github.com/org/repo.git
git remote rename origin upstream
git remote remove old
git remote show origin           # branch'lar, tracking, nimasi eskirgani
```

## fetch, pull, push

```bash
git fetch origin                 # yangi commit'larni yuklab oladi; working tree'da HECH NARSA o'zgarmaydi
git pull                         # fetch + joriy branch'ga merge
git pull --rebase                # fetch + sizning commit'laringizni ustiga qayta o'ynatish (chiziqli tarix)
git push                         # joriy branch'ni u kuzatayotgan remote branch'ga yuboradi
git push -u origin feature-tls   # yangi branch'ning birinchi push'i: yaratadi va tracking o'rnatadi
git push --all; git push --tags
git push --force-with-lease      # remote tarixni qayta yozish - faqat o'zingizga tegishli branch uchun
```

`fetch` doim xavfsiz; `pull` esa fayllaringizni o’zgartiradi. Nimadir
g’alati tuyulsa, `git fetch` qiling, so’ng `git log --oneline
HEAD..origin/main` nima kelayotganini qabul qilishdan oldin aniq
ko’rsatadi.

| Xabar | Ma’nosi |
|---|---|
| `Updates were rejected because the remote contains work that you do not have locally` | kimdir avval push qilgan - `git pull --rebase`, keyin push |
| `fatal: The current branch X has no upstream branch` | birinchi push - `git push -u origin X` |
| `Permission denied (publickey)` | SSH kalitingiz hostda yo’q yoki noto’g’ri kalit - `ssh -T git@github.com` |
| `Please tell me who you are` | `git config user.name/user.email` |
| `refusing to merge unrelated histories` | ikkita mustaqil repozitoriy - agar ataylab qilayotgan bo’lsangiz `git pull --allow-unrelated-histories` |

## Tag’lar

```bash
git tag v1.0                          # yengil
git tag -a v1.0 -m "Release 1.0"      # izohli (muallif, sana, xabar bor) - shuni afzal ko'ring
git tag                               # ro'yxat
git show v1.0
git push origin v1.0; git push --tags
git checkout v1.0                     # detached HEAD: qarang, bu yerda commit qilmang
```

## Sistem administratorga mos ish tartibi

```bash
git switch -c fix-logrotate          # o'zgarish uchun branch
vi /etc/logrotate.d/nginx
git add -A && git commit -m "Rotate nginx logs daily, keep 14"
git switch main && git merge fix-logrotate && git branch -d fix-logrotate
git push
```

Kichik branch, bitta o’zgarish, merge, push. Remote’siz serverda esa oxirgi
satrsiz xuddi shunday - tarix baribir sizniki.

:::exam-tip
LFCS’ning Git topshiriqlari shu darajada qoladi: branch yarating, unda
commit qiling, orqaga merge qiling, remote qo’shing, push qiling. `git
switch -c`, `git merge`, `git remote add`, `git push -u origin <branch>`.
Konfliktni qanday yakunlashni biling (tahrirlash, `git add`, `git commit`) -
odamlarni to’xtatadigan yagona qadam shu.
:::

## O’zingizni tekshiring

1. Branch nima va fast-forward bilan merge commit orasidagi farq nima?
2. `git fetch` `git pull` ham qiladigan nimani bajaradi va nimani
   bajarmaydi?
3. Konfliktli faylni tahrirladingiz. Merge’ni yakunlaydigan ikkita buyruq
   qaysi?
