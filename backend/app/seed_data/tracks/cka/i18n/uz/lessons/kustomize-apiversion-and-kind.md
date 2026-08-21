## Sarlavha

Har bir `kustomization.yaml` Kubernetes obyektinikiga o’xshab ko’rinadigan,
lekin obyekt bo’lmagan ikkita qator bilan boshlanadi:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
```

Ular Kustomize’ga faylning qolgan qismi qaysi sxemaga bo’ysunishini aytadi.
Ularni tashlab ketsangiz, hozirgi versiyalar aynan shu qiymatlarni taxmin
qiladi va ogohlantirish chiqaradi; yozsangiz, fayl aniq bo’ladi va
linter’dan toza o’tadi. Yozing.

| Maydon | Qiymat |
|---|---|
| `apiVersion` | `kustomize.config.k8s.io/v1beta1` - "beta" turganiga qaramay, ishlatiladigan yagona versiya |
| `kind` | base yoki overlay uchun `Kustomization`; qayta ishlatiladigan ixtiyoriy qism uchun `Component` (`kustomize.config.k8s.io/v1alpha1`) |

```yaml
# component, komponentlar darsi uchun
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
```

## Bu Kubernetes obyekti emas

`kubectl apply -f kustomization.yaml` ishlamaydi:

```
error: unable to recognize "kustomization.yaml": no matches for kind "Kustomization" in version "kustomize.config.k8s.io/v1beta1"
```

- chunki API server’da bunday resource yo’q. Bu faylni klient tomonida `-k`
bilan Kustomize o’qiydi. Shu xato chiqsa, demak `-k` kerak bo’lgan joyda
`-f` ishlatgansiz.

## Kustomize daraxtida uchraydigan boshqa obyekt bo’lmagan YAML

JSON 6902 shaklidagi inline va fayldagi patch’lar ham obyekt emas - ular
amallar ro’yxati:

```yaml
- op: replace
  path: /spec/replicas
  value: 3
```

Strategic merge patch fayllari esa, aksincha, qisman obyekt
**hisoblanadi**: ularda `apiVersion`, `kind` va `metadata.name` bo’ladi,
shuning uchun Kustomize ular qaysi resource’ni o’zgartirishini biladi:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
```

Ikkalasi ham patch darslarida ko’rib chiqiladi; bu yerdagi yagona gap shuki,
kustomize fayllari daraxtida uch xil YAML bo’ladi - haqiqiy obyektlar,
kustomization’ning o’zi va patch’lar - va sarlavha qaysi biri ekanini aytib
turadi.

:::tip
Eski qo’llanmalar sarlavhani umuman tashlab ketadi va `resources:` o’rniga
`bases:`, `patches:` o’rniga `patchesStrategicMerge:`, `labels` o’rniga
`commonLabels` ko’rsatadi. Ular hali ham ishlaydi (eskirgani haqidagi
ogohlantirish bilan), lekin siz hozirgi shakllarni yozing - `kustomize edit`
aynan shularni yaratadi va imtihonning namuna fayllari ham shularni
ishlatadi.
:::

## O’zingizni tekshiring

1. Kustomization’ning `apiVersion`/`kind` juftligi qanday va u nima uchun
   kerak?
2. kustomization.yaml faylini `kubectl apply -f` bilan bersangiz nima
   bo’ladi va nega?
3. Qayta ishlatiladigan ixtiyoriy qism qaysi `kind`ni ishlatadi?
