## Fayl - bu inode; nom esa link

Linux filesystem’ida faylning **ma’lumotlari va metama’lumotlari**
(ruxsatlar, egasi, timestamp’lar, hajmi, bloklari qayerdaligi) raqam bilan
belgilanadigan **inode** ichida yashaydi. Directory ichidagi **fayl nomi** -
shunchaki inode raqamiga ishora qiluvchi yozuv. Xuddi shu inode’ga ishora
qiluvchi ikkinchi yozuv yarating - va faylning ikkita nomi bo’ladi. O’sha
ikkinchi yozuv - **hard link**.

```
 directory yozuvlari               inode 5281 (mode, egasi, hajmi, bloklari, link soni = 2)
   report.txt  ──▶ 5281 ◀──  final.txt
```

```bash
echo "draft" > report.txt
ln report.txt final.txt             # ln TARGET LINKNAME
ls -li report.txt final.txt
# 5281 -rw-r--r-- 2 ahmad ahmad 6 Aug 19 10:00 final.txt
# 5281 -rw-r--r-- 2 ahmad ahmad 6 Aug 19 10:00 report.txt
```

`-i` inode’ni ko’rsatadi: **xuddi shu raqam**. Mode’dan keyingi `2` -
**link soni**, ya’ni bu inode’ga nechta nom ishora qilishi.

## Oqibatlari

- Istalgan nom orqali tahrirlang, o’zgarish ikkalasida ham ko’rinadi -
  chunki fayl bitta.
- `rm report.txt` **bitta nomni** olib tashlaydi; link soni 1 ga tushadi;
  ma’lumot esa qoladi va `final.txt` orqali erishiladi. Ma’lumot faqat
  hisob **0** ga yetganda va uni ochiq ushlab turgan jarayon qolmaganda
  bo’shatiladi.
- Ruxsatlar, egasi, hajmi va timestamp’lar inode’ga tegishli, shuning uchun
  har bir nom orqali bir xil; bittasi orqali `chmod` - hammasi orqali
  `chmod`.
- `ls -l` directory’lar uchun ham link sonini ko’rsatadi: uning ichidagi `.`
  va har bir subdirectory’ning `..` unga ishora qiladi, shuning uchun bo’sh
  directory’da 2, uchta subdirectory’lisida 5 bo’ladi.

```bash
stat report.txt                     # Inode: 5281   Links: 2
find / -samefile report.txt 2>/dev/null    # bu inode'ning har bir nomi
find /data -inum 5281
find /data -type f -links +1        # bittadan ortiq nomga ega fayllar
rm report.txt; cat final.txt        # hamon "draft"
```

## Hard link’larning cheklovlari

| Nima qila olmaydi | Nega |
|---|---|
| **filesystem’lar** orasida link qilish | inode raqami faqat o’z filesystem’i ichida ma’noga ega; `ln: failed to create hard link ... Invalid cross-device link` |
| **directory**’ga link qilish | daraxtda tsikllarga yo’l ochardi; faqat `.` va `..`’ga ruxsat (ularni kernel yaratadi) |
| qaysi nom "asli" ekanini aytish | bunday nom yo’q; hamma nomlar teng |

Soft link’lar (keyingi dars) aynan shu ikki holat uchun mavjud.

## Nega ulardan foydalaniladi

- Ikki joyda ko’rinishi va nusxasi ajralib ketmasdan **bir xil** qolishi
  kerak bo’lgan fayl (ikki nom ostidagi konfiguratsiya; kutubxonaning
  versiyali va versiyasiz nomi).
- Backup sxemalari (`rsync --link-dest`, `cp -al`): o’zgarmagan fayllar -
  oldingi snapshot’ga hard link, shuning uchun deyarli o’zgarmaydigan 100 GB
  daraxtning o’nta kunlik backup’i 100 GB’dan sal ko’proq turadi.
- O’chirishdan himoya: bitta nom mavjud ekan, ma’lumot ham mavjud.

```bash
cp -al snapshot.0 snapshot.1        # har bir faylni hard link qilib bir zumda "nusxalash"
```

## ls -l ni linklarni hisobga olib o’qish

```
-rw-r--r-- 2 ahmad ahmad 6 Aug 19 10:00 final.txt
           ^ link soni: bu inode uchun 2 ta nom
drwxr-xr-x 5 ahmad ahmad 4096 ... projects   <- 5 = . + 3 ta subdirectory'ning .. yozuvlari... (2 + 3)
```

:::exam-tip
"`/etc/app/config`’ga `/etc/app/config.bak` nomli hard link yarating" -
bu `ln /etc/app/config /etc/app/config.bak`. `ls -li` bilan tekshiring -
inode bir xil, link soni 2. Topshiriqdagi ikki yo’l turli
filesystem’larda bo’lsa (aytaylik, `/boot` va `/home`), hard link imkonsiz
va javob - symbolic link; topshiriq odatda qaysi biri kerakligini aytadi.
:::

## O’zingizni tekshiring

1. `ls -l`’da ruxsatlardan keyingi raqam nimani anglatadi va u nolga
   yetganda faylning ma’lumotlariga nima bo’ladi?
2. Hard link qila olmaydigan ikki narsani ayting.
3. `/var/app/data.db` bilan bir xil faylga ishora qiluvchi har bir nomni
   qanday topasiz?
