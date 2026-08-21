## Uchta stream

Har bir jarayon uchta ochiq file descriptor bilan boshlanadi:

| FD | Nomi | Sukut bo’yicha |
|---|---|---|
| **0** | stdin | klaviatura |
| **1** | stdout | terminal |
| **2** | stderr | terminal |

Redirection ularni fayllarga, bir-biriga yoki boshqa jarayonga qayta
yo’naltiradi. Butun g’oya shundan iborat va kichik buyruqlarni bir-biriga
ulash imkonini beradigan narsa ham shu.

## Chiqish

```bash
ls > files.txt              # stdout faylga, faylni QIRQIB tashlab
ls >> files.txt             # oxiriga qo'shadi
ls /nope 2> errors.txt      # stderr faylga
ls /nope 2>> errors.txt     # stderr oxiriga qo'shiladi
ls > out.txt 2> err.txt     # alohida-alohida
ls > all.txt 2>&1           # stderr STDOUT HOZIR KETAYOTGAN JOYGA - tartib muhim
ls &> all.txt               # bash'dagi xuddi shuning qisqartmasi
ls &>> all.txt              # oxiriga qo'shadigan qisqartma
command > /dev/null         # stdout'ni tashlab yuboradi
command 2> /dev/null        # xatolarni tashlab yuboradi (find, /proc ustidagi grep...)
command > /dev/null 2>&1    # hammasini tashlab yuboradi
command 2>&1 > file         # "hammasi faylga" uchun NOTO'G'RI: stderr terminalga, stdout faylga ketadi
```

`2>&1` "FD 2 ni FD 1 ning **hozirgi holatidagi** nusxasi qil" degani. Uni
stdout redirect’idan **keyin** qo’ying, aks holda nusxa terminalniki
bo’ladi.

## Kirish

```bash
sort < unsorted.txt              # stdin fayldan
mysql -u root < dump.sql
while read line; do echo "$line"; done < /etc/passwd

cat <<EOF > /etc/motd            # here-document: EOF gacha bo'lgan matn
Welcome to $(hostname)
EOF

cat <<'EOF' > script.sh          # qo'shtirnoqli chegara: o'zgaruvchi OCHILMAYDI
echo $HOME stays literal
EOF

cat <<-EOF                       # <<- boshidagi TAB'larni olib tashlaydi (chekinishli skriptlar uchun)
	indented
	EOF

grep root <<< "root:x:0:0"       # here-string: bitta qator stdin sifatida
```

## Pipe’lar

```bash
ps aux | grep nginx | wc -l
journalctl -u sshd | grep Failed | awk '{print $NF}' | sort | uniq -c | sort -rn
cat /etc/passwd | cut -d: -f1 | sort        # (cat ortiqcha: cut -d: -f1 /etc/passwd | sort)
command1 |& command2                        # bash: stdout VA stderr'ni pipe qiladi
command 2>&1 | less                         # xuddi shuning portativ shakli
```

Pipe chap buyruqning **stdout**’ini o’ng buyruqning **stdin**’iga ulaydi;
stderr’ni o’zingiz redirect qilib kiritmasangiz, u pipe’ga tushmaydi.
Pipeline’ning exit status’i **oxirgi** buyruqniki, `set -o pipefail`
qo’yilmagan bo’lsa.

## tee: faylga *va* keyingisiga

```bash
ls | tee files.txt                      # faylga yozadi VA ekranga chiqaradi
ls | tee -a files.txt                   # oxiriga qo'shadi
make 2>&1 | tee build.log | tail -20    # hammasini logga yozadi, oxirini ko'rsatadi
echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-fw.conf    # pipe'dan root egalik qiladigan faylni yozish yo'li
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null
```

`sudo command > /root/file` ishlamaydi - faylni **shell**, sizning
nomingizdan, sudo ishga tushishidan oldin ochadi. `| sudo tee file` -
yechim.

## Boshqa file descriptor’lar

```bash
exec 3> /tmp/log             # FD 3 ni yozish uchun ochadi
echo "hello" >&3
exec 3>&-                    # yopadi
command 3>&1 1>&2 2>&3       # stdout va stderr'ni almashtiradi
diff <(sort a) <(sort b)     # process substitution: har biri /dev/fd/N "fayl"ga aylanadi
wc -l < <(grep ERROR log)
comm -13 <(sort a) <(sort b)
```

## Bilib qo’yishga arziydigan mayda-chuydalar

```bash
command < /dev/null              # buyruqqa hech qanday kirish bermaydi (daemon'lar, cron uchun)
: > file                        # faylni o'chirmasdan nolga qirqadi
> file                          # xuddi shu, qisqaroq
nohup long-job > job.log 2>&1 &  # logout'dan keyin ham yashaydi, hammasini logga yozadi
yes | apt install pkg            # abadiy 'y' beradi
xargs                            # stdin'ni ARGUMENTLARGA aylantiradi (stdin emas): find ... | xargs rm
echo /etc/*.conf | xargs ls -l
```

`xargs` farqi muhim: `echo file | rm` hech nima qilmaydi (rm stdin
o’qimaydi); `echo file | xargs rm` esa uni o’chiradi.

:::exam-tip
Redirection deyarli har bir imtihon topshirig’i ichida uchraydi:
"chiqishni /root/x.txt ga saqlang" → `> /root/x.txt`; "xatolar bilan
birga" → `> file 2>&1`; "oxiriga qo’shing" → `>>`; "pipeline’dan root
egalik qiladigan faylni yozing" → `| sudo tee`. Natijani `cat` bilan
tekshiring - bo’sh fayl odatda chiqish stderr’da bo’lganini va siz faqat
stdout’ni redirect qilganingizni bildiradi.
:::

## O’zingizni tekshiring

1. Nega `command 2>&1 > file` xatolarni faylga yubormaydi?
2. Root talab qiladigan faylga pipeline ichidan qanday yozasiz?
3. `|` va `xargs` orasidagi farq nima?
