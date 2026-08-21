## Tugaydigan ish

Deployment’lar Pod’larni abadiy ishlab turadigan qilib saqlaydi. Ba’zi ishlar
esa buning aksi: oxirigacha bajariladi, muvaffaqiyat yoki nosozlik haqida
xabar beradi va to’xtaydi. Ma’lumotlar bazasi migratsiyasi, hisobot, paketli
o’zgartirish, backup. Bu - **Job**; jadval bo’yicha ishlaydigan Job esa -
**CronJob**.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: report
spec:
  completions: 1           # nechta muvaffaqiyatli Pod kerak
  parallelism: 1           # bir vaqtda nechtasi ishlashi mumkin
  backoffLimit: 4          # Job Failed deb belgilangunicha nechta nosozlik
  activeDeadlineSeconds: 600
  ttlSecondsAfterFinished: 3600   # tugaganidan bir soat keyin Job va Pod'larini tozalaydi
  template:
    spec:
      restartPolicy: Never          # majburiy: Never yoki OnFailure - hech qachon Always emas
      containers:
        - name: report
          image: reports:1.4
          command: ["python", "monthly.py"]
```

```bash
kubectl create job report --image=reports:1.4 -- python monthly.py
kubectl create job one-off --from=cronjob/backup          # CronJob'ning ishini hozir bajaradi
kubectl get jobs
# NAME     COMPLETIONS   DURATION   AGE
# report   1/1           42s        2m
kubectl get pods -l job-name=report
kubectl logs job/report
kubectl delete job report                                 # uning Pod'larini ham o'chiradi
```

## restartPolicy va backoffLimit

Job’da `Always` ruxsat etilmaydi - har doim qayta ishga tushadigan Pod hech
qachon tugamaydi. Qolgan ikkita yaroqli qiymat "qayta urinish" nimani
anglatishini o’zgartiradi:

| `restartPolicy` | Nosozlikda | `backoffLimit` nimani sanaydi |
|---|---|---|
| `OnFailure` | **konteyner** o’sha Pod ichida qayta ishga tushiriladi | konteyner restart’lari (RESTARTS ustunida ko’rinadi) |
| `Never` | Pod Failed holatida qoldiriladi va **yangi Pod** yaratiladi | ishlamagan Pod’lar (ular `get pods`’da to’planib boradi - loglar uchun foydali) |

Har ikki holatda ham `backoffLimit`’ga yetilgach, Job’ning condition’larida
`Failed` paydo bo’ladi va u urinishni to’xtatadi.

## completions va parallelism

```yaml
completions: 5
parallelism: 2
```

"Menga beshta muvaffaqiyatli ishga tushirish kerak; bir vaqtda ko’pi bilan
ikkitasi ishlasin." Bu - qat’iy belgilangan completion soni. Har bir Pod
elementlar tugaguncha ularni navbatdan olaveradigan work queue uchun
`completions`’ni qo’ymang, faqat `parallelism`’ni bering; bunda **istalgan**
Pod muvaffaqiyatli tugab, qolganlari chiqib ketganda Job tugaydi. Indexed
Job’lar (`completionMode: Indexed`) har bir Pod’ga `JOB_COMPLETION_INDEX`
beradi, shunda beshta Pod ma’lumotning beshdan bir qismini alohida qayta
ishlay oladi.

:::exam-tip
Imtihondagi Job topshiriqlari raqamlar haqida: "5 marta ishlasin, 2 tasi
parallel, 3 ta nosozlikdan keyin to’xtasin" degani `completions: 5,
parallelism: 2, backoffLimit: 3`. `kubectl create job --completions` kabi
flaglar yo’q - `$do` bilan generatsiya qiling, `spec` ostiga uchta qatorni
qo’shing va apply qiling.
:::

## CronJob’lar

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "30 2 * * *"            # har kuni 02:30, cron sintaksisi, kontroller vaqt mintaqasida (kubeadm'da UTC)
  timeZone: "Asia/Tashkent"         # ixtiyoriy, 1.27 dan beri
  concurrencyPolicy: Forbid         # Allow | Forbid | Replace
  startingDeadlineSeconds: 300
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: backup-tool:3.1
              args: ["--target", "s3://bucket/nightly"]
```

```bash
kubectl create cronjob backup --image=backup-tool:3.1 --schedule="30 2 * * *" -- /backup.sh
kubectl get cronjobs
# NAME     SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE   AGE
kubectl get jobs --watch                 # har bir ishga tushish backup-<timestamp> nomli Job
kubectl patch cronjob backup -p '{"spec":{"suspend":true}}'   # uni pauza qiladi
```

To’g’ri tushunish kerak bo’lgan qism - ichma-ichlik: CronJob **spec** →
`jobTemplate` → Job **spec** → `template` → Pod **spec**. Uchta `spec:`
kaliti, har biri o’z darajasida. `kubectl explain
cronjob.spec.jobTemplate.spec.template.spec --recursive` sizning do’stingiz.

`concurrencyPolicy` navbatdagi vaqt kelganda oldingi ishga tushirish hali
tugamagan bo’lsa nima bo’lishini hal qiladi: `Allow` yana bittasini boshlaydi,
`Forbid` yangisini o’tkazib yuboradi, `Replace` eskisini o’ldiradi. Backup’lar
uchun `Forbid` kerak.

:::warning
Cron sintaksisi beshta maydondan iborat - daqiqa soat oyning-kuni oy
haftaning-kuni - va `*/5 * * * *` degani "har besh daqiqada". `30 2 * * *`
kabi jadval, agar `timeZone` boshqacha aytmasa, **klaster** vaqt mintaqasida
02:30 da ishlaydi; ko’pchilik klasterlarda bu UTC, ya’ni Toshkentdan 5 soat
orqada.
:::

## O’zingizni tekshiring

1. Nega Job’ning Pod shabloni `restartPolicy: Always`’dan foydalana olmaydi?
2. `restartPolicy: Never` va `backoffLimit: 3` bilan hech qachon
   muvaffaqiyatli tugamaydigan Job uchun nechta Pod ko’rishingiz mumkin?
3. "Har dushanba soat 06:00 da" uchun `schedule`’ni yozing va o’zi bilan
   ustma-ust tushmasligi kerak bo’lgan job uchun qaysi `concurrencyPolicy`’ni
   qo’yasiz?
