## Ikkalasi ham hal qiladigan muammo

Sizda bitta ilova uchun Deployment, Service, ConfigMap va Ingress bor. Ular
sizga `dev`, `staging` va `prod`’da kerak - har xil replika soni, image,
hostname va resurs limitlari bilan. To’rtta faylni uch marta nusxalash o’n
ikkita fayl beradi va ular birinchi haftadayoq bir-biridan uzoqlashadi.

**Helm** va **Kustomize** - ikkita asosiy javob va ular qarama-qarshi
yondashuvni tanlagan.

| | Helm | Kustomize |
|---|---|---|
| G’oya | joy egallovchilari bor **shablonlar**, values faylidan to’ldiriladi | overlay va patch’lar bilan o’zgartiriladigan **oddiy YAML** bazalar |
| Birlik | **chart** - shablonlar, standart values va metama’lumot bor paket | `kustomization.yaml` bor katalog |
| O’rnatish | `helm install name chart -f values.yaml` | `kubectl apply -k dir/` |
| Holatni kuzatadi | ha - reviziya, tarix va rollback bilan **release**’lar | yo’q - u YAML render qiladi; qolganini `kubectl apply` qiladi |
| Tarqatish | chart repozitoriylari va registry’lari (Artifact Hub) | Git, istalgan katalog |
| O’rganish egri chizig’i | Go shablonlari, chart tuzilishi | YAML va bir nechta tushuncha |
| kubectl ichida bormi | yo’q (alohida CLI) | **ha** (`kubectl apply -k`, `kubectl kustomize`) |

## Helm bir ekranda

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-db bitnami/postgresql --set auth.postgresPassword=secret
helm list
helm upgrade my-db bitnami/postgresql --set primary.persistence.size=20Gi
helm rollback my-db 1
helm uninstall my-db
```

Kimdir bir marta chart yozgan - PostgreSQL’ga kerak bo’lgan har bir obyekt
uchun shablon, har bir sozlagich esa value sifatida ochilgan - siz faqat
o’zingizga kerak bo’lgan uchta value’ni belgilaysiz. Helm’ning kuchi shunda:
**boshqalarning dasturiy ta’minotini o’rnatish**.

## Kustomize bir ekranda

```
app/
  base/
    deployment.yaml   service.yaml   kustomization.yaml   (resources: [deployment.yaml, service.yaml])
  overlays/
    dev/   kustomization.yaml   (resources: [../../base]; replicas patch: 1; namePrefix: dev-)
    prod/  kustomization.yaml   (resources: [../../base]; replicas patch: 5; images: newTag 2.1.0)
```

```bash
kubectl kustomize overlays/prod | less       # render qilingan YAML'ni ko'ring
kubectl apply -k overlays/prod
```

Baza - haqiqiy, to’g’ri YAML, uni o’z holicha apply qilsa bo’ladi; overlay’lar
faqat nimasi farq qilishini tasvirlaydi. Kustomize’ning kuchi shunda: shablon
tilisiz **o’z manifestlaringizni muhitlar bo’ylab boshqarish**.

## Qaysi birini qachon ishlatish

- Uchinchi tomon komponentini o’rnatish (ingress controller, cert-manager,
  monitoring, ma’lumotlar bazasi) → **Helm** - chart allaqachon bor, undan
  foydalaning.
- O’z ilovangizning manifestlari, Git’da, har bir muhit uchun → **Kustomize**
  - o’qiladigan diff’lar, shablon xatolari yo’q.
- Ikkalasini birga ishlatish odatiy hol: `helm template` chart’ni YAML’ga
  render qiladi va Kustomize uni patch qiladi (kustomization’dagi
  `helmCharts:` aynan shuni qiladi); Argo CD va Flux ikkalasini ham nativ
  qo’llab-quvvatlaydi.

:::exam-tip
2025-yilgi CKA ikkalasini ham dasturga qo’shdi: "klaster komponentlarini
o’rnatish uchun Helm va Kustomize’dan foydalanish". `helm repo add / install / upgrade / rollback /
uninstall` va resources, transformer hamda patch ishlatadigan kustomization
bilan `kubectl apply -k`’ni kuting. Keyingi darslar har birini alohida ko’rib
chiqadi, laboratoriyalar esa buni qo’lingizga o’rgatadi.
:::

## Bu haftaning xaritasi

| Kunlar | Mavzu |
|---|---|
| Helm | nima ekani, uni o’rnatish, Helm 2 va Helm 3, komponentlar, chart’lar, kundalik buyruqlar, custom values, hayot tsikli |
| Kustomize | muammo va g’oya, Helm bilan solishtirish, o’rnatish, `kustomization.yaml`, output, kataloglar, transformerlar, patch’lar, overlay’lar, komponentlar |

## O’zingizni tekshiring

1. Helm va Kustomize manifestlarni qanday qayta ishlatishi orasidagi farqni
   bitta jumlada ayting.
2. Qaysi biri nima o’rnatganini kuzatadi va rollback qila oladi, qaysi biri
   kubectl ichiga qurilgan?
3. Sizga cert-manager o’rnatish kerak va o’z API’ingizni uchta muhitda deploy
   qilish kerak. Qaysi ish uchun qaysi asbob?
