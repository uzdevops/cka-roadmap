## CRD va kontroller, birga paketlangan

**Operator** - bu CRD (yoki bir nechtasi) va ular ustida harakat qiladigan
kontroller: ikkalasi bitta o’rnatiladigan narsa sifatida birga yetkaziladi va
muayyan dasturiy ta’minotni qanday boshqarishni o’zida kodlaydi. etcd
operatori etcd klasterini yaratishni, a’zo qo’shishni, backup olishni va
yo’qolgan a’zodan keyin tiklashni biladi - chunki kimdir o’sha operatsion
bilimni kontrollerga yozib qo’ygan. Siz bitta obyekt yaratasiz:

```yaml
apiVersion: etcd.database.coreos.com/v1beta2
kind: EtcdCluster
metadata:
  name: example
spec:
  size: 3
  version: "3.5.12"
```

qolganini esa operator qiladi, shu jumladan odam tunda soat 3 da qilishiga
to’g’ri keladigan ishlarni ham.

```
operator = CRD'lar (lug'at) + kontroller (runbook, kod ko'rinishida) + RBAC + uni ishga tushiruvchi Deployment
```

Butun g’oya shu. Prometheus, cert-manager, Strimzi (Kafka), PostgreSQL
operatorlari, Argo CD - har biri operator: uni o’rnatasiz va murakkab bir
narsani boshqaradigan yangi kind paydo bo’ladi.

## Siz aslida nimani o’rnatasiz

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.0/cert-manager.yaml
kubectl get crd | grep cert-manager         # Certificate, Issuer, ClusterIssuer, ...
kubectl get deploy -n cert-manager          # kontroller(lar)
kubectl get clusterrole | grep cert-manager # o'z kind'larini kuzatish va Secret yaratish uchun kerak bo'lgan RBAC
```

Helm ham xuddi shuni `helm install` bilan qiladi; **Operator Lifecycle Manager
(OLM)** va **OperatorHub.io** - yangilanish kanallari bilan operatorlar uchun
katalog va o’rnatuvchi. Ostidagi artefakt esa bir xil: CRD’lar, RBAC va
Deployment.

## Imkoniyat darajalari

Operator Framework operator qancha ish qilishini baholashga yaraydigan
shkalada tasvirlaydi:

| Daraja | Operator nima qila oladi |
|---|---|
| 1 - Oddiy o’rnatish | dasturiy ta’minotni o’z custom resursidan deploy qiladi |
| 2 - Uzluksiz yangilash | uni joyida yangilaydi |
| 3 - To’liq hayot tsikli | backup oladi, tiklaydi, fail over qiladi |
| 4 - Chuqur ko’rinish | metrikalar, alertlar, loglarni qayta ishlashni beradi |
| 5 - Avtopilot | o’zini masshtablaydi va sozlaydi |

Ko’pchilik ochiq kodli operatorlar 2-3 darajada. Operator qaysi darajani da’vo
qilishini bilish sizga qancha ish hali ham o’z zimmangizda ekanini aytadi.

## Nega bu klaster administratoriga muhim

- **Siz ularning ko’pini boshqarasiz.** Ingress kontrollerlar, cert-manager,
  monitoring, storage, service mesh’lar - zamonaviy klaster operatorlar uchun
  operatsion tizimga o’xshaydi.
- **Ular imtiyozlar bilan keladi.** Operatorning ClusterRole’i ko’pincha keng
  bo’ladi (u siz uchun Secret, Service, Deployment yaratishi kerak).
  O’rnatishdan oldin uni o’qing; bu `kubectl get clusterrole <name> -o yaml`.
- **Ular o’zicha buziladi.** Pending holatida qotib qolgan custom obyekt
  operatorning kontrolleri o’chganini, ruxsati yetishmayotganini yoki
  ishlamayotganini bildiradi - javob obyektda emas, uning Pod loglarida.
- **Yangilashning ikki yarmi bor.** Operatorning o’z versiyasi va u
  boshqaradigan narsaning versiyasi; ikkalasidan birini ko’tarishdan oldin
  operatorning eslatmalarini o’qing.

:::exam-tip
CKA sizdan atamalarni - CRD, custom kontroller, operator, OperatorHub -
bilishni va mexanik qismini bajarishni kutadi: manifestdan o’rnatish, u
qo’shgan CRD’larni ro’yxatlash, custom obyekt yaratish, kontroller loglarini
topish. U sizdan operator yozishni kutmaydi. Topshiriqda "X operatorini
o’rnating va Y yarating" deyilsa, avval uning manifestidan CRD kind’larini
o’qing (apply qilgandan keyin `kubectl api-resources | grep <group>`), keyin
obyektni yozish uchun `kubectl explain <kind>`.
:::

## Operatorni o’rnatish uchun minimal ro’yxat

```bash
# 1. u nimalarni qo'shadi?
curl -sL <manifest-url> | grep -E "^kind:" | sort | uniq -c
# 2. u nimalar qila oladi?
curl -sL <manifest-url> | grep -A30 "kind: ClusterRole" | head -60
# 3. o'rnating, so'ng qismlarini tasdiqlang
kubectl apply -f <manifest-url>
kubectl get crd,deploy,sa -A | grep <operator-name>
kubectl logs -n <ns> deploy/<operator> | tail
```

## O’zingizni tekshiring

1. Operatorga bundan oldingi ikki darsning atamalari bilan bir qatorda ta’rif
   bering.
2. Operator o’rnatdingiz va custom obyekt pending holatida qolib ketdi.
   Qayerga qaraysiz?
3. O’rnatishdan oldin operatorning ClusterRole’ini o’qishning ikkita sababini
   ayting.
