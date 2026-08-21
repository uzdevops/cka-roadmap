## Bitta muammoning ikki yarmi

Uchta jamoani tasavvur qiling - blue, red, green - har birining o’ziga
ajratilgan node’i bor, ustiga qolgan hamma uchun ikkita umumiy node. Siz
shuni xohlaysiz:

1. jamoa Pod’lari **faqat** o’z node’ida ishlasin va
2. boshqalarning Pod’lari jamoa node’lariga **hech qachon** tushmasin.

Bu ikki mexanizmning birortasi ikkalasini ham qilmaydi.

## Faqat taint va toleration

Uchta node’ni taint qiling (`color=blue:NoSchedule` va hokazo) va har bir
jamoaning Pod’lariga mos toleration bering. 2-talab bajarildi: tasodifiy Pod
jamoa node’iga tusha olmaydi. Lekin 1-talab bajarilmadi - blue Pod blue
node’ga *chidaydi*, unga *tortilmaydi*, va bemalol umumiy node’ga
joylashtirilishi mumkin.

```
blue Pod ──▶ blue node   ✓ ruxsat
blue Pod ──▶ shared node ✓ bunga ham ruxsat   <- bo'shliq
red  Pod ──▶ blue node   ✗ chidalmagan taint
```

## Faqat node affinity

Node’larga label qo’ying (`color=blue`) va har bir jamoaning Pod’lariga o’z
rangi bo’yicha required node affinity bering. 1-talab bajarildi: blue Pod’lar
faqat blue node’ga boradi. Lekin 2-talab bajarilmadi - umuman affinity
qoidasi yo’q Pod istalgan joyga, shu jumladan blue node’ga ham tushishi
mumkin.

```
blue Pod ──▶ blue node   ✓ talab qilingan
blue Pod ──▶ shared node ✗ affinity mos kelmadi
other Pod ─▶ blue node   ✓ hech nima to'smaydi   <- bo'shliq
```

## Ikkalasi birga

Jamoa node’larini taint qiling **va** label qo’ying; jamoa Pod’lariga
toleration **va** affinity bering. Endi blue Pod’lar faqat blue’ga bora oladi
(affinity) va u yerga faqat blue Pod’lar bora oladi (taint). Na taint, na
label’i bor umumiy node’lar qolgan hammani qabul qiladi.

| | taint/toleration | node affinity | ikkalasi |
|---|---|---|---|
| boshqalarni node’imdan uzoq tutish | ha | yo’q | ha |
| o’z Pod’larimni node’imda ushlab turish | yo’q | ha | ha |

```yaml
# blue jamoasining Pod shabloni
spec:
  tolerations:
    - key: color
      operator: Equal
      value: blue
      effect: NoSchedule
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: color
                operator: In
                values: [blue]
```

```bash
kubectl taint nodes node01 color=blue:NoSchedule
kubectl label  nodes node01 color=blue
```

:::exam-tip
Topshiriq *ajratilgan* node’ni tasvirlasa - "node03 da faqat monitoring
Pod’lari ishlashi mumkin va ular o’sha yerda ishlashi kerak" - u ikkalasini
so’rayapti. Agar gaplardan faqat bittasi bo’lsa, u faqat bittasini so’rayapti.
Qaysi fe’llar borligiga qarang: "shu yerda ishlashi kerak" = affinity;
"boshqa hech narsa u yerda ishlamasin" = taint.
:::

## Qachon qaysi biriga qo’l urish kerak

| Vaziyat | Vosita |
|---|---|
| umumiy workload’larni maxsus node’lardan (GPU, control plane, texnik xizmat) uzoq tutish | taint |
| aniq workload’larni aniq node’larga joylashtirish | nodeSelector / affinity |
| ikkalasi | ikkalasi |
| "shart" emas, "afzal" | preferred affinity (taint’larda teskari yo’nalish uchun `PreferNoSchedule` bor) |
| texnik xizmat uchun node’ni bo’shatish | `kubectl drain` (bu siz uchun bajarib beriladigan `NoExecute` taint va eviction) |

:::tip
`kubectl cordon` - niqoblangan taint: u node’ni unschedulable deb belgilaydi
(`node.kubernetes.io/unschedulable:NoSchedule`). `kubectl drain` ustiga
eviction qo’shadi. Node `SchedulingDisabled` ko’rsatganda va uni kim taint
qilgan deb o’ylayotganingizda buni bilish yordam beradi.
:::

## O’zingizni tekshiring

1. Faqat taint va toleration bilan blue Pod blue node’da ishlashini
   kafolatlay olasizmi? Nega yo’q?
2. Faqat node affinity bilan blue node’da boshqa hech narsa ishlamasligini
   kafolatlay olasizmi? Nega yo’q?
3. Topshiriqda "`mon` Deployment’ining Pod’lari node03 da ishlashi kerak va u
   yerda boshqa Pod’lar ishlamasligi kerak" deyilgan. Kerak bo’ladigan har bir
   buyruq va YAML blokni sanab bering.
