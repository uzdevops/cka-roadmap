## Shablonlash va patch qilish

Ikkalasi ham "bitta manifestlar to’plami, ko’p muhit" muammosini hal qiladi.
Buni ular qarama-qarshi tomondan qiladi.

**Helm** manifestlarni teshiklari bor shablonga aylantiradi va teshiklarni
value’lardan to’ldiradi:

```yaml
replicas: {{ .Values.replicaCount }}
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

**Kustomize** manifestlarni butun qoldiradi va ularga kiritiladigan
o’zgarishlarni tasvirlaydi:

```yaml
# overlays/prod/kustomization.yaml
resources: [../../base]
images: [{name: myapp, newTag: "2.1.0"}]
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
    target: {kind: Deployment, name: myapp}
```

| | Helm | Kustomize |
|---|---|---|
| baza YAML’i | o’z holicha yaroqsiz (`{{ }}` bor) | yaroqli, o’z holicha apply qilinadi |
| ifoda kuchi | Go shablonlari qila oladigan hamma narsa: tsikl, shart, funksiya | faqat overlay va patch ifodalay oladigani - ataylab shunday |
| paketlash va ulashish | chart’lar, repozitoriylar, versiyalar | Git’dagi kataloglar |
| release kuzatuvi, rollback | ha | yo’q - `kubectl apply` va `kubectl rollout` |
| uchinchi tomon dasturlari | ekotizim: minglab chart’lar | nimani vendor qilsangiz, shuni patch qilasiz |
| xatolar qanday ko’rinadi | shablon yaroqsiz YAML render qiladi; xato yozilgan value jimgina standart qiymatga tushadi | patch hech narsani nishonga olmaydi (xato) yoki noto’g’ri narsani oladi (`kubectl kustomize` chiqishida ko’rinadi) |
| o’rnatish | alohida CLI | kubectl ichida |

## Halol murosa

Helm shablonlari *hamma narsani* qila oladi va muammo ham shunda: katta chart
- bu shablon tilida yozilgan dastur va u nima ishlab chiqarishini bilish uchun
uni o’qish ishga tushirish bilan barobar. Kustomize *kamroq* narsa qila oladi
va gap ham shunda: baza o’qiladi, overlay - bu diff va `kubectl kustomize`
sizga butun natijani ko’rsatadi, ortidan quvadigan mantiq yo’q.

**O’zingiz yozmagan dasturiy ta’minot** uchun Helm ekotizimi yutadi - chart
muallifi sozlagichlarni allaqachon ochib qo’ygan. **O’zingizga tegishli
manifestlar** uchun Kustomize ularni oddiy holida saqlaydi.

## Ikkalasi birga

```yaml
# kustomization.yaml
helmCharts:
  - name: ingress-nginx
    repo: https://kubernetes.github.io/ingress-nginx
    version: 4.11.1
    releaseName: ingress
    namespace: ingress-nginx
    valuesInline:
      controller:
        replicaCount: 2
patches:
  - patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value: {role: edge}
    target: {kind: Deployment, name: ingress-ingress-nginx-controller}
```

```bash
kubectl kustomize --enable-helm . | kubectl apply -f -
```

Chart’ni render qiling, keyin render qilingan chiqishni chart value’lari
ifodalay olmaydigan narsalar bilan patch qiling. GitOps asboblari (Argo CD,
Flux) bu shaklni nativ qo’llab-quvvatlaydi.

:::tip
Jamoa uchun yaxshi qoida: platforma komponentlarini o’rnatishga Helm,
o’z ilovalaringizga Kustomize - va ikkovi hech qachon urishmaydi, chunki
ular har xil kataloglarga egalik qiladi.
:::

## O’zingizni tekshiring

1. Nega Kustomize bazasi o’z holicha apply qilinadi, Helm chart’ining
   shablonlari esa yo’q?
2. Prometheus o’rnatish uchun qaysi asbobni tanlaysiz va o’z API’ingizni
   uchta klasterga deploy qilish uchun qaysinisini?
3. Helm chart’ining chiqishini Kustomize bilan qanday patch qilasiz?
