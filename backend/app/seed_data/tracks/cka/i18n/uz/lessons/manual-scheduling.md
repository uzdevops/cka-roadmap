## Scheduler aslida nima qiladi

Scheduler’ni eng soddasiga tushirsangiz, u bitta yozuv qiladi: `nodeName`i
bo’sh Pod’ning `spec.nodeName` maydonini to’ldiradi. Nomi ko’rsatilgan
node’dagi kubelet "menga tegishli Pod" ni ko’radi va uni ishga tushiradi.
Qolgan hamma narsa - filtrlash, ball berish, affinity, taint’lar - o’sha
bitta yozuvdan **oldingi** mulohaza.

Demak, scheduler yo’q bo’lsa, o’sha yozuvni o’zingiz qila olasiz.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  nodeName: node02          # <- qo'lda joylashtirilgan
  containers:
    - name: nginx
      image: nginx
```

Buni `kubectl apply` qiling va Pod scheduler uni umuman ko’rmasdan node02 da
ishlaydi. Hech qanday filtrlash bo’lmaydi: agar node02 da resurs yetmasa yoki
Pod chidamaydigan taint bo’lsa, kubelet baribir urinib ko’radi - Pod ishga
tushmasligi mumkin, lekin u node’ga biriktirilgan bo’ladi.

## Bu qachon kerak bo’ladi

- **Scheduler ishlamayapti** (nosozlikni bartaraf etish topshirig’i) va
  scheduler’ni tuzatishdan oldin sizga *hozir* ishlayotgan Pod kerak.
- Siz node’ni tekshirayapsiz va Pod aynan o’sha yerda bo’lishini xohlaysiz,
  bahssiz.
- Siz static Pod yozayapsiz - ular har doim "qo’lda" joylashtiriladi, chunki
  kubelet ularni fayldan ishga tushiradi.

:::warning
`nodeName` yaratish paytida beriladi. Uni mavjud Pending Pod’ga `kubectl edit`
bilan qo’sha olmaysiz - Pod mavjud bo’lgach, bu maydon o’zgarmas. O’chirib
qayta yarating yoki quyidagi Binding obyektidan foydalaning.
:::

## Binding obyekti

Scheduler API serverga aslida **Binding** yuboradi: "bu Pod, ana u node" deb
aytadigan kichkina obyekt. Siz ham xuddi shuni yubora olasiz:

```yaml
apiVersion: v1
kind: Binding
metadata:
  name: nginx                 # Pod'ning nomi
target:
  apiVersion: v1
  kind: Node
  name: node02
```

```bash
# Pod'ning binding subresource'iga POST qiling
curl --header "Content-Type: application/json" --request POST \
  --data '{"apiVersion":"v1","kind":"Binding","metadata":{"name":"nginx"},"target":{"apiVersion":"v1","kind":"Node","name":"node02"}}' \
  http://localhost:8001/api/v1/namespaces/default/pods/nginx/binding/
```

(Boshqa terminalda `kubectl proxy` `localhost:8001`’ni beradi.) Bu allaqachon
mavjud va Pending holatdagi Pod’ni bog’laydi. Imtihonda o’chirib-qayta yaratish
yo’li tezroq, agar topshiriqda Pod qayta yaratilmasligi kerak deb aytilmagan
bo’lsa.

## Amaliy ketma-ketlik

```bash
kubectl get pods                         # nginx Pending holatda
kubectl describe pod nginx | tail -5     # umuman event yo'q -> uni hech kim joylashtirmagan
kubectl get pods -n kube-system | grep scheduler   # u umuman bormi?

kubectl get pod nginx -o yaml > nginx.yaml
# spec ostiga  nodeName: node02  qo'shing
kubectl replace --force -f nginx.yaml
kubectl get pod nginx -o wide            # node02 da Running
```

:::exam-tip
"Event yo’q" - asosiy belgi. Scheduler *ko’rgan*, lekin joylashtira olmagan
Pod’da sababni tushuntiradigan `FailedScheduling` event bo’ladi. Events
bo’limi bo’sh bo’lgan Pod’ga esa umuman qaralmagan: scheduler yo’q yoki Pod
mavjud bo’lmagan `schedulerName`’ni so’ragan. Qo’lda joylashtirish alomatni
tuzatadi; scheduler’ning o’zini ham tuzatishni unutmang, aks holda keyingi Pod
ham qotib qoladi.
:::

## nodeName bilan nima qila olmaysiz

- Ishlayotgan Pod’ni ko’chirish. "Qayta rejalashtirish" degan narsa yo’q; siz
  uni o’chirasiz va kimdir (kontroller yoki siz) uni qaytadan yaratadi.
- Deployment’ning Pod’larini biriktirish. Pod shablonidagi `nodeName`
  **har bir** replikani bitta node’ga biriktiradi - ruxsat etilgan, lekin
  kamdan-kam kerak. "Shu turdagi node afzal" uchun sizga nodeSelector yoki
  affinity kerak (keyingi darslar), ular baribir scheduler orqali o’tadi.

## O’zingizni tekshiring

1. Scheduler qaysi bitta maydonni yozadi va qaysi komponent unga javob beradi?
2. Pod Pending holatda va Events bo’limi bo’sh. Bu sizga nima deydi va uni
   ishga tushirish uchun ikkita variantingiz qanday?
3. Nega Deployment’ning Pod shablonidagi `nodeName` deyarli har doim xato?
