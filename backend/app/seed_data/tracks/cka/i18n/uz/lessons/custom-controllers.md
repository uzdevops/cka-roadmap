## Resursni ish qildiradigan tsikl

Har bir o’rnatilgan kind’ning kontrolleri bor: o’sha kind obyektlarini
kuzatadigan, ular so’ragan narsani mavjud narsa bilan solishtiradigan va
farqni yopadigan jarayon. ReplicaSet kontrolleri `replicas: 3` ni va ikkita
Pod’ni ko’radi-da, bittasini yaratadi. **Custom kontroller** - sizning
CRD’ingiz uchun yozilgan o’sha tsiklning o’zi.

```
FlightTicket'larni kuzat ──▶ har biri uchun: bron qilinganmi? ──yo'q──▶ aviakompaniya API'sini chaqir, status yoz
         ▲                                                            │
         └────────────────────────── requeue ◀────────────────────────┘
```

U API serverdan tashqarida yashaydi - odatda klasterdagi Deployment sifatida,
o’z kind’ini kuzatish uchun RBAC berilgan ServiceAccount ostida ishlaydi - va
API server bilan boshqa har qanday klient kabi gaplashadi. Uni o’ldirsangiz,
obyektlar joyida qoladi; ular shunchaki u qaytguncha ustida harakat
qilinmay turadi.

## Kodning shakli

Kontrollerlar Go’da **client-go** ustiga yoziladi, chunki butun mexanizm
o’sha yerda:

- **informer** obyektlarning lokal keshini saqlaydi va add/update/delete’da
  callback chaqiradi - shunda kontroller API serverni so’rab turmaydi;
- **work queue** e’tibor talab qiladigan obyektlarning kalitlarini yig’adi;
- **reconcile** funksiyasi bitta kalitni oladi, obyektni o’qiydi, haqiqatni
  o’qiydi va ularni moslashtiradigan ishni bajaradi - idempotent tarzda,
  chunki u yana chaqiriladi.

```go
func (c *Controller) reconcile(key string) error {
    ticket, err := c.lister.FlightTickets(ns).Get(name)
    if errors.IsNotFound(err) { return nil }          // deleted; nothing to do
    if ticket.Status.Booked { return nil }            // already done
    ref, err := airline.Book(ticket.Spec.From, ticket.Spec.To, ticket.Spec.Number)
    if err != nil { return err }                      // error -> requeued with backoff
    ticket.Status.Booked, ticket.Status.Reference = true, ref
    _, err = c.client.FlightsV1().FlightTickets(ns).UpdateStatus(ctx, ticket, metav1.UpdateOptions{})
    return err
}
```

Pattern ReplicaSet kontrollerdan tortib eng kichik operatorgacha bir xil:
**level-triggered** (u o’zini uyg’otgan hodisaga emas, joriy holatga qaraydi),
**idempotent** (ikki marta ishlashi xavfsiz), **eventually consistent**
(haqiqat mos kelguncha qayta urinaveradi).

Faqat `reconcile` yozishingiz uchun karkasni generatsiya qiladigan
freymvorklar: **kubebuilder** va **Operator SDK** (Go), **Metacontroller**
(webhook orqali istalgan tilda), **kopf** (Python).

## Administratorga bundan nima kerak

CKA’da kontroller yozmaysiz. Siz ular bilan to’lgan klasterlarni boshqarasiz
va yuzaga keladigan savollar operatsion bo’ladi:

| Savol | Qayerga qarash kerak |
|---|---|
| kontroller ishlayaptimi? | `kubectl get deploy -n <its namespace>`, uning Pod loglari |
| nega custom obyektim ishlanmayapti? | kontroller loglari; uning RBAC’i (`auth can-i list <kind> --as system:serviceaccount:<ns>:<sa>`) |
| u nima qildi? | `kubectl describe <kind> <name>` - yaxshi kontrollerlar **status** va **events** yozadi |
| u nimadir bilan urishayaptimi? | doim ortga o’zgarib turadigan obyekt - ikkita kontroller yoki kontroller va odam |

```bash
kubectl logs -n flights deploy/flightticket-controller -f
kubectl describe ft my-flight-ticket | tail      # kontroller yozgan Status va Events
kubectl get ft my-flight-ticket -o jsonpath='{.status}'
```

:::tip
`status` va `Events` yozadigan kontrollerni tekshirib bo’ladi; yozmaydigani -
qora quti. O’rnatish uchun operatorni baholayotganda uning obyektlaridan
biriga `kubectl describe` qiling va u sizga biror narsa aytadimi, qarang.
:::

## Status - obyektning kontrollerga tegishli yarmi

`spec` - sizniki, ya’ni siz xohlagan narsa. `status` - kontrollerniki, ya’ni u
kuzatgani va qilgani. Bu bo’linish kontrollerga `status` subresursini berish
bilan ta’minlanadi (CRD’da `subresources: {status: {}}`): shunda u sizning
spec’ga kiritayotgan tahrirlaringiz bilan poyga qilmasdan statusni yangilay
oladi va RBAC unga statusni yozishga ruxsat berib, spec’ga bermasligi mumkin.
Har bir o’rnatilgan kind shunday ishlaydi; `kubectl get deploy` kontroller
to’ldirgan READY/AVAILABLE ustunlarini shuning uchun ko’rsatadi.

## O’zingizni tekshiring

1. Kontroller bir gapda nima qiladi va u to’xtasa mavjud custom obyektlarga
   nima bo’ladi?
2. Nega `reconcile` idempotent bo’lishi shart?
3. Custom obyekt ishlanmasdan turibdi. Birinchi tekshiradigan ikkita narsani
   ayting.
