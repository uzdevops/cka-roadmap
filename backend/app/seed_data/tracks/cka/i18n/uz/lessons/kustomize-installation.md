## Allaqachon bor

Kustomize 1.14 versiyasidan beri `kubectl` tarkibida keladi:

```bash
kubectl kustomize ./overlays/prod          # render
kubectl apply -k ./overlays/prod           # render qiladi va qo'llaydi
kubectl delete -k ./overlays/prod
kubectl diff -k ./overlays/prod
kubectl version --client                   # yangi kubectl'da kustomize versiyasi ham ko'rsatiladi
```

Ko’pchilik ish uchun shuning o’zi yetarli va imtihonga ham shundan ortig’i
kerak emas.

## Alohida binary

`kubectl` ichiga o’rnatilgan nusxa loyihadan bir necha reliz orqada qoladi va
unda ba’zi flag’lar yo’q (`--enable-helm`, `--load-restrictor`, `edit`
subbuyruqlari). Alohida `kustomize` esa xuddi shu engine, faqat eng yangisi:

```bash
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
kustomize version
```

```bash
kustomize build ./overlays/prod                    # == kubectl kustomize
kustomize build ./overlays/prod | kubectl apply -f -
kustomize edit set image myapp=myapp:2.1.0         # kustomization.yaml'ni siz uchun tahrirlaydi
kustomize edit add resource deployment.yaml
kustomize edit set namespace prod
kustomize create --autodetect                      # katalogdagi fayllardan kustomization.yaml yasaydi
```

`edit` subbuyruqlari kustomization’ni skript orqali o’zgartirish usuli - CI’da
keng tarqalgan `kustomize edit set image app=app:$SHA && git commit` iborasi
ko’plab pipeline’lar versiyani ko’taradigan yo’ldir.

## Qachon qaysi biri

| Nima uchun | Buyruq |
|---|---|
| nimani qo’llashingizni ko’rish uchun render qilish | `kubectl kustomize dir/` |
| qo’llash | `kubectl apply -k dir/` |
| `--enable-helm` yoki eng yangi imkoniyatlar kerak | `kustomize build` |
| kustomization’ga o’zgartirishlarni avtomatlashtirish | `kustomize edit ...` |

:::exam-tip
`kubectl apply -k`’ga **ichida `kustomization.yaml` bo’lgan** katalog kerak,
faylning o’zi emas. `kubectl apply -k overlays/prod/kustomization.yaml`
ishlamaydi; `kubectl apply -k overlays/prod` ishlaydi. Va `-k` bu `-f` emas:
kustomization.yaml faylini `-f` bilan bersangiz, kubectl uni Kubernetes
obyekti sifatida qo’llashga urinadi va "no kind Kustomization" xatosini
beradi.
:::

## O’zingizni tekshiring

1. kubectl bilan Kustomize ishlatish uchun nima o’rnatishingiz kerak?
2. Qaysi ikkita buyruq overlay’ni render qiladi va qo’llaydi?
3. `kubectl apply -k overlays/prod/kustomization.yaml` ishlamaydi. Nega?
