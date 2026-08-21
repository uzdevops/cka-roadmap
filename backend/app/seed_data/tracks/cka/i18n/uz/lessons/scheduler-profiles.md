## Scheduler - bu pluginlar quvuri

Scheduler joylashtiradigan har bir Pod bir xil **kengaytma nuqtalari**
ketma-ketligidan o’tadi va ularning har birida bir to’plam **plugin** ishlaydi:

```
queueSort ─▶ preFilter ─▶ filter ─▶ postFilter ─▶ preScore ─▶ score ─▶ reserve ─▶ permit ─▶ preBind ─▶ bind ─▶ postBind
```

| Nuqta | U yerda nima ishlaydi | O’rnatilgan pluginlarga misol |
|---|---|---|
| `queueSort` | kutayotgan navbatni tartiblaydi | `PrioritySort` (PriorityClass bo’yicha) |
| `filter` | Pod’ni qabul qila olmaydigan node’larni rad etadi | `NodeResourcesFit`, `NodeName`, `NodeUnschedulable`, `TaintToleration`, `NodeAffinity`, `VolumeBinding` |
| `postFilter` | hech bir node o’tmasa nima qilish kerakligi | `DefaultPreemption` |
| `score` | omon qolganlarni 0-100 oralig’ida baholaydi | `NodeResourcesBalancedAllocation`, `ImageLocality`, `NodeAffinity`, `PodTopologySpread` |
| `reserve` / `permit` | resurslarni ushlab turadi, kerak bo’lsa kutadi | (gang scheduling, extender’lar) |
| `bind` | `nodeName`’ni yozadi | `DefaultBinder` |

Bu bosqichda o’rgangan hamma narsangiz - o’sha pluginlardan biri: taint’lar -
filter’dagi `TaintToleration`, node affinity - filter va score’dagi
`NodeAffinity`, request’lar - filter’dagi `NodeResourcesFit`, priority -
`PrioritySort` va `DefaultPreemption`.

## Profil: nomlangan plugin konfiguratsiyasi

**Profil** - bu `schedulerName` va har bir nuqtada qaysi pluginlar yoqilgan
yoki o’chirilganini ko’rsatuvchi ro’yxat. Bitta scheduler jarayoni bir nechta
profilga xizmat qila oladi, Pod esa `spec.schedulerName` bilan bittasini
tanlaydi.

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: default-scheduler

  - schedulerName: no-image-locality
    plugins:
      score:
        disabled:
          - name: ImageLocality

  - schedulerName: bin-packing
    plugins:
      score:
        disabled:
          - name: "*"
        enabled:
          - name: NodeResourcesFit
      # va bu plugin to'la node'larni afzal ko'rishi uchun sozlanadi:
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
```

`disabled: [{name: "*"}]` o’sha kengaytma nuqtasidagi sukut to’plamini
tozalaydi; keyin `enabled`’siz xohlaganlarini tartib bilan qaytarib qo’shadi.
`pluginConfig` esa pluginga argumentlar uzatadi.

## Faylni ulash

Konfiguratsiya scheduler’ga `--config` bilan uzatiladi. kubeadm klasterida
sukut bo’yicha scheduler’da bunday fayl yo’q - demak, uni siz qo’shasiz:

```bash
# 1. konfiguratsiyani node'ga yozing, masalan /etc/kubernetes/scheduler-config.yaml
# 2. static Pod manifestini tahrirlang
vim /etc/kubernetes/manifests/kube-scheduler.yaml
```

```yaml
    command:
      - kube-scheduler
      - --config=/etc/kubernetes/scheduler-config.yaml
      # --authentication-kubeconfig / --authorization-kubeconfig / --kubeconfig flaglarini saqlang
      #   YOKI kubeconfig'ni faylning clientConnection.kubeconfig ichiga ko'chiring
    volumeMounts:
      - mountPath: /etc/kubernetes/scheduler-config.yaml
        name: scheduler-config
        readOnly: true
volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler-config.yaml
      type: FileOrCreate
    name: scheduler-config
```

kubelet scheduler’ni qayta ishga tushiradi; `kubectl logs
kube-scheduler-controlplane -n kube-system` u yuklagan profillarni ko’rsatadi.

:::exam-tip
Bu yerda ikkita xato eng ko’p vaqt oladi. Konfiguratsiya faylini static Pod
ichiga **mount qilishni** unutish - scheduler "no such file" bilan
crash-loop’ga tushadi. Va `profiles` ro’yxatidan `default-scheduler`’ni
tushirib qoldirish - shunda klasterdagi har bir oddiy Pod Pending bo’lib
qoladi, chunki bu nomga endi hech kim xizmat qilmaydi. Sukut profilni
ro’yxatda doim saqlang.
:::

## Nega ikkinchi scheduler emas, profil

| | ikkinchi scheduler jarayoni | ikkinchi profil |
|---|---|---|
| RBAC, ServiceAccount, leader election | ha, hammasi kerak | kerak emas |
| boshqa koddan foydalana oladi | ha | yo’q - bir xil binary |
| ikki scheduler bitta Pod uchun kurashish xavfi | nomlar to’qnashsa mumkin | yo’q |
| nima uchun yaxshi | vendor/maxsus scheduler’lar | workload’ga qarab o’rnatilgan pluginlarni yoqish/o’chirish |

"Menga boshqacha joylashtirish kerak" degan ehtiyojlarning ko’pi - aslida
profil.

## O’zingizni tekshiring

1. Taint va toleration’larni amalga oshiradigan kengaytma nuqtasi va pluginni
   ayting.
2. `score` ostidagi `disabled: [{name: "*"}]` nima qiladi va undan keyin nima
   kelishi shart?
3. kube-scheduler static Pod’iga konfiguratsiya faylini qo’shdingiz va
   klasterdagi har bir yangi Pod Pending bo’lib qoldi. Katta ehtimol bilan
   nimani tushirib qoldirdingiz?
