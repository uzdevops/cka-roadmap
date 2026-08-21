## Kundalik buyruqlar

```bash
helm search hub wordpress                       # Artifact Hub
helm search repo bitnami/wordpress --versions   # siz qo'shgan repo
helm show chart bitnami/wordpress               # Chart.yaml
helm show values bitnami/wordpress              # values.yaml - sozlagichlar
helm show readme bitnami/wordpress
```

### install

```bash
helm install my-site bitnami/wordpress                           # release nomi, chart
helm install my-site bitnami/wordpress -n web --create-namespace
helm install my-site bitnami/wordpress --version 22.1.0          # chart versiyasini qotiring
helm install my-site ./wordpress-22.1.0.tgz                      # lokal paket
helm install my-site ./my-chart-dir                              # lokal katalog
helm install my-site bitnami/wordpress --generate-name           # nomni Helm qo'ysin
helm install my-site bitnami/wordpress --wait --timeout 5m       # Pod'lar Ready bo'lguncha kutadi
```

```
NAME: my-site
LAST DEPLOYED: Mon Aug 18 10:00:00 2026
NAMESPACE: web
STATUS: deployed
REVISION: 1
NOTES:
  ... (the chart's NOTES.txt: how to reach it, how to get the password)
```

### list, status, get

```bash
helm list -n web                  # namespace'dagi release'lar
helm list -A                      # hamma joyda
helm list -A --failed             # faqat buzilganlari
helm status my-site -n web        # yana NOTES, --show-resources bilan resurslar ham
helm get manifest my-site -n web  # aynan nima apply qilingani
helm get values my-site -n web    # siz belgilaganingiz
helm get notes my-site -n web
helm history my-site -n web
```

### upgrade

```bash
helm upgrade my-site bitnami/wordpress -n web --set replicaCount=2       # value'larni o'zgartirish (chart versiyasi repo indeksidagi eng oxirgisi bo'lib qoladi)
helm upgrade my-site bitnami/wordpress -n web --version 22.2.0           # chart versiyasini o'zgartirish
helm upgrade my-site bitnami/wordpress -n web -f prod.yaml --reuse-values
helm upgrade --install my-site bitnami/wordpress -n web                   # yo'q bo'lsa o'rnatadi, bor bo'lsa yangilaydi - CI idiomasi
```

### rollback va uninstall

```bash
helm rollback my-site 1 -n web
helm uninstall my-site -n web
helm uninstall my-site -n web --keep-history       # reviziyalarni tekshirish uchun saqlab qoladi
```

`uninstall` release yaratgan har bir obyektni o’chiradi, **faqat**
`helm.sh/resource-policy: keep` annotatsiyasi qo’yilganlaridan tashqari -
ko’p ma’lumotlar bazasi chart’laridagi PersistentVolumeClaim’lar shunday - shu
sababli tasodifiy uninstall’dan keyin ma’lumot saqlanib qoladi.

## Natijaga kubectl uslubida qarash

```bash
kubectl get all -n web -l app.kubernetes.io/instance=my-site
kubectl get all -n web -l app.kubernetes.io/managed-by=Helm
```

Konvensiyalarga amal qiladigan chart’lar hamma narsani release nomi
(`instance`) va `managed-by=Helm` bilan belgilaydi, shuning uchun release
yaratgan obyektlar bitta selektor narigi tomonida turadi.

## Install ishdan chiqqanda

```bash
helm install my-site bitnami/wordpress -n web --dry-run --debug | less    # apply qilishdan oldin YAML va xatoni ko'ring
helm list -n web -a                                                        # -a ishdan chiqqan/kutilayotgan release'larni ham ko'rsatadi
helm status my-site -n web
helm uninstall my-site -n web        # ishdan chiqqan install ham release yozuvini yaratgan; qayta urinishdan oldin uni o'chiring
```

| Xabar | Nimani anglatadi |
|---|---|
| `Error: INSTALLATION FAILED: cannot re-use a name that is still in use` | release mavjud (ehtimol ishdan chiqqan) - `helm list -a`, uninstall qiling yoki boshqa nom tanlang |
| `Error: failed to download "bitnami/x"` | repo qo’shilmagan yoki yangilanmagan, yoki bunday versiya yo’q |
| `Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress` | qotib qolgan pending release - oxirgi yaxshi reviziyaga `helm rollback` qiling yoki `helm history` bilan yozuvni tuzating |
| `Error: context deadline exceeded` | `--wait` vaqti tugadi: Pod’lar Ready emas - `kubectl get pods` |

:::exam-tip
Imtihonning Helm topshiriqlari shunday yangraydi: "Y repo’sidan X chart’ini
N namespace’ida Z release sifatida K=V value bilan o’rnating", "Z release’ni
A chart versiyasiga upgrade qiling", "Z’ni 1-reviziyaga rollback qiling",
"Z’ni uninstall qiling". Har biri shu sahifadagi bitta buyruq, har doim `-n`
bilan. Oxirida `helm list -A` holatni isbotlaydi.
:::

## O’zingizni tekshiring

1. Release mavjud yoki mavjud emasligiga qarab uni o’rnatadigan **yoki**
   yangilaydigan yagona buyruqni yozing.
2. `helm uninstall` nimani qoldirib ketadi va nega?
3. Install yarim yo’lda ishdan chiqdi va qayta urinishda nom band deb
   aytilyapti. Nima qilasiz?
