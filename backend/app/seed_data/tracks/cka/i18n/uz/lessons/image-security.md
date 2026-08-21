## Image nomi aslida nima deydi

```
image: nginx
```

quyidagining qisqartmasi

```
image: docker.io/library/nginx:latest
       └──┬───┘ └──┬──┘ └─┬─┘ └──┬──┘
       registry  user/org image   tag
```

| Qism | Ko’rsatilmagandagi sukut qiymati |
|---|---|
| registry | `docker.io` (Docker Hub) |
| user / tashkilot | `library` (Docker’ning rasmiy image’lari) |
| tag | `latest` |

Demak, `nginx` `docker.io/library/nginx:latest`’ni tortadi;
`kodekloud/webapp-color` `docker.io/kodekloud/webapp-color:latest`’ni tortadi;
`registry.k8s.io/kube-apiserver:v1.30.2` esa to’liq yozilgan. Yopiq registry -
shunchaki birinchi bo’lagi boshqa: `myregistry.io:5000/apps/web:1.4`.

:::warning
`latest` "eng yangi" degani emas - u ham boshqalari kabi oddiy tag, o’sha nom
ostida nima push qilingan bo’lsa, o’sha. Production manifestlari tag’ni (yoki
digest’ni: `nginx@sha256:abc...`) qat’iy belgilaydi, kubelet qayta tortadimi
yoki yo’qmi degan qarorni esa `imagePullPolicy` qiladi: `Always` (`latest`
uchun sukut), `IfNotPresent` (boshqa tag’lar uchun sukut), `Never`.
:::

## Yopiq registry’dan image tortish

Image’ni node’dagi konteyner runtime’i tortadi, demak unga hisob
ma’lumotlari kerak. Kubernetesda siz ularni
`kubernetes.io/dockerconfigjson` turidagi Secret sifatida berasiz va Pod’dan
unga murojaat qilasiz:

```bash
kubectl create secret docker-registry private-reg-cred \
  --docker-server=myregistry.io:5000 \
  --docker-username=dock_user \
  --docker-password=dock_password \
  --docker-email=dock_user@myregistry.io
```

```yaml
spec:
  imagePullSecrets:
    - name: private-reg-cred
  containers:
    - name: web
      image: myregistry.io:5000/apps/web:1.4
```

```bash
kubectl set image deployment/web web=myregistry.io:5000/apps/web:1.4
kubectl patch deployment web -p '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"private-reg-cred"}]}}}}'
# yoki kubectl edit deployment web va blokni template.spec ostiga qo'shing
```

Yoki uni ServiceAccount’ga biriktiring - o’sha akkauntdan foydalanadigan har
bir Pod uni meros qilib oladi:

```bash
kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"private-reg-cred"}]}'
```

Bu Secret - shunchaki boshqa o’ramdagi `~/.docker/config.json`:

```bash
kubectl get secret private-reg-cred -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d
# {"auths":{"myregistry.io:5000":{"username":"dock_user","password":"dock_password","auth":"..."}}}
```

## Pull nosozliklarini o’qish

```bash
kubectl get pods
# web-7c6f   0/1   ErrImagePull      -> keyin ImagePullBackOff
kubectl describe pod web-7c6f | tail -8
```

| Hodisada nima deyilgan | Sababi |
|---|---|
| `... not found` / `manifest unknown` | nom yoki tag noto’g’ri |
| `unauthorized` / `authentication required` | yopiq image, `imagePullSecrets` yo’q yoki noto’g’ri |
| `dial tcp ... i/o timeout` / `no such host` | registry node’dan ko’rinmaydi yoki registry nomida xato bor |
| `x509: certificate signed by unknown authority` | shaxsiy CA’li registry; unga Kubernetes emas, **node’ning** runtime’i ishonishi kerak (containerd `hosts.toml`) |

:::exam-tip
Topshiriqda "image X manzilidagi yopiq registry’da, hisob ma’lumotlari mana
bu" deyilgan bo’lsa, bu aniq ikki qadam: `kubectl create secret
docker-registry` va Pod shablonidagi `imagePullSecrets`. `--docker-server`
qiymatiga e’tibor bering - u image nomidagi registry bilan, porti bilan
birga, mos kelishi kerak.
:::

## Tortishdan tashqarisi: ishga tushirayotganingizga ishonish

CKA tortish bilan tugaydi; CKS undan uzoqroq boradi, lekin umumiy manzara bir
abzatsga arziydi:

- **Digest’ni qat’iy belgilang**, shunda image tag ostida o’zgarib ketmaydi.
- Admission siyosati bilan **registry’larni cheklang** (`myregistry.io`’dan
  kelmagan image’larni rad etadigan validating webhook yoki
  `ValidatingAdmissionPolicy`).
- CI’da **image’larni skanerlang**; ularni **imzolang** va imzolarni
  admission’da tekshiring.
- Konteynerlarni **securityContext** bilan non-root sifatida ishga tushiring
  - keyingi darslar.

## O’zingizni tekshiring

1. `kodekloud/webapp-color`’ni to’liq yozilgan shakliga yoying.
2. Registry hisob ma’lumotlarini qaysi turdagi Secret saqlaydi va Pod
   spec’ining qayerida unga murojaat qilinadi?
3. `unauthorized` bilan kelgan `ErrImagePull` - qaysi ikki narsani
   tekshirasiz?
