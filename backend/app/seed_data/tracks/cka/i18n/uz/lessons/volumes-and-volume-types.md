## Pod’ga storage ulash

Konteynerning fayl tizimi konteyner bilan birga o’ladi. **Volume** - bu Pod
konteynerlariga berilgan katalog; uning umri va orqasidagi storage esa uning
**turi** bilan aniqlanadi. Spec’da ikkita yarmi bor:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-number
spec:
  containers:
    - name: alpine
      image: alpine
      command: ["sh", "-c", "shuf -i 0-100 -n 1 >> /opt/number.out"]
      volumeMounts:                  # 2. SHU konteynerda qayerda paydo bo'ladi
        - name: data
          mountPath: /opt
  volumes:                           # 1. volume'ning o'zi, Pod darajasida
    - name: data
      hostPath:
        path: /data
        type: DirectoryOrCreate
```

`volumes` uni Pod uchun bir marta e’lon qiladi; uni xohlagan har bir konteyner
nomi bo’yicha `volumeMounts` yozuvini qo’shadi. Bir nechta konteyner bitta
volume’ni mount qilishi mumkin - multi-container pattern’i shu.

## Uchraydigan turlar

| Turi | Nima ustida turadi | Umri | Nima uchun |
|---|---|---|---|
| `emptyDir` | node’dagi katalog (yoki `medium: Memory` bilan RAM) | Pod | vaqtinchalik joy, konteynerlar orasida uzatish |
| `hostPath` | node’dagi yo’l | node diski | `/var/log` yoki Docker soketi kerak bo’lgan node agentlari; ilova ma’lumoti uchun **emas** |
| `configMap`, `secret`, `downwardAPI`, `projected` | API obyektlari | Pod | konfiguratsiya fayllar sifatida |
| `persistentVolumeClaim` | claim qaysi PV’ga bog’langan bo’lsa, o’sha | Pod’dan uzoqroq | haqiqiy ma’lumot - keyingi uchta dars |
| `nfs` | NFS export’i | server | umumiy fayl tizimi, hamma joyda ishlaydigan eng oddiy "tarmoq storage’i" |
| `local` | PV orqali aniq bir node’dagi disk | node | node affinity bilan tez lokal disklar |
| `csi` | CSI driver’i | driver’niki | PVC odatda nimaga aylanadi, o’sha |

`emptyDir` va `hostPath` - yoddan bilish kerak bo’lgan ikkitasi.

```yaml
volumes:
  - name: cache
    emptyDir: {}
  - name: cache-in-memory
    emptyDir:
      medium: Memory
      sizeLimit: 256Mi
```

```yaml
volumes:
  - name: node-logs
    hostPath:
      path: /var/log
      type: Directory          # "" | DirectoryOrCreate | Directory | FileOrCreate | File | Socket
```

## hostPath nega masshtablanmaydi

`hostPath` **Pod qaysi node’ga tushsa, o’sha node’ning** katalogini mount
qiladi. Bitta node’li labda buni doimiy storage’dan ajratib bo’lmaydi; uch
node’li klasterda esa Pod node02 ga qayta rejalashtiriladi va bo’sh katalogni
topadi. Bundan tashqari u Pod’ga node fayl tizimini o’qish va yozish imkonini
beradi - `baseline` Pod Security uni shuning uchun taqiqlaydi. O’rinli
ishlatilishlari: node’ning o’ziga chindan muhtoj DaemonSet’lar (log
jo’natuvchilar, monitoring agentlari, CSI node plugin’lari) va
`/etc/kubernetes/pki` ni mount qiladigan control plane’ning static Pod’lari.

:::warning
"Pod boshqa node’ga qayta rejalashtirilganda ham ma’lumot saqlanib qolishi
kerak" degan topshiriq - qisqa YAML qanchalik jozibador ko’rinmasin - hostPath
topshirig’i **emas**. Bu PVC topshirig’i.
:::

## Pod nimani mount qilganini o’qish

```bash
kubectl get pod random-number -o jsonpath='{.spec.volumes}'
kubectl describe pod random-number | grep -A6 "Mounts:\|Volumes:"
kubectl exec random-number -- df -h /opt
kubectl exec random-number -- ls -la /opt
```

:::exam-tip
Volume’lar va mount’lar ishlab turgan Pod’da, spec’ning ko’p qismi kabi,
**o’zgarmas**. "X Pod’iga volume qo’shing" - bu get-yaml, tahrirlash,
`replace --force`. Tekshiruvchilar ikki narsaga qaraydi: `volumeMounts` yozuvi
to’g’ri **konteyner** ostida turibdimi va uning `name` qiymati `volumes`
ichidagi yozuvga aynan mos keladimi.
:::

## O’zingizni tekshiring

1. Pod spec’ida `volumes` qayerga, `volumeMounts` qayerga yoziladi?
2. `emptyDir` qachon yo’qoladi, `hostPath` katalogi qachon?
3. Ko’p node’li klasterda ma’lumotlar bazasining ma’lumoti uchun `hostPath`
   nega noto’g’ri javob?
