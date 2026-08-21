## Har bir node’dagi agent

Har bir node - worker ham, control plane ham - bitta kubelet ishlatadi. Bu Pod
**bo’lmagan** yagona Kubernetes komponenti: u host’dagi systemd xizmati,
chunki birorta Pod paydo bo’lishidan oldin allaqachon nimadir ishlab turishi
kerak, o’sha nimadir - kubelet. Uning vazifasi:

1. Node’ni API server’da **ro’yxatdan o’tkazadi** va heartbeat yuborib turadi
   (sukut bo’yicha node holati har o’n sekundda).
2. API server’da shu node’ga biriktirilgan Pod’larni **kuzatadi**
   (`spec.nodeName` uning nomiga teng).
3. Har biri uchun: image’larni CRI orqali yuklab oladi, sandbox va
   konteynerlarni yaratadi, volume’larni mount qiladi, muhit o’zgaruvchilari va
   Secret’larni kiritadi.
4. Konteynerlarni **probe** qiladi va restart policy bo’yicha ularni qayta
   ishga tushiradi.
5. Pod holati va resurs sarfini orqaga **xabar qiladi**.
6. Manifest katalogidan **static Pod**’larni ishga tushiradi - kubeadm
   klasterlarida butun control plane shu mexanizm orqali ko’tariladi.

```
API server ◀──▶ kubelet ──CRI──▶ containerd ──▶ konteynerlar
                   │
                   └── /etc/kubernetes/manifests  (static Pod'lar)
```

## U qanday ishlaydi va qayerda sozlanadi

```bash
systemctl status kubelet
journalctl -u kubelet -f                              # uning loglari - kubelet uchun kubectl logs yo'q
ps -ef | grep kubelet | tr ' ' '\n' | grep -- --       # u qaysi flag'lar bilan ishga tushgani
```

kubeadm node’ida muhim konfiguratsiya uchta faylga bo’lingan:

| Fayl | Nimani saqlaydi |
|---|---|
| `/var/lib/kubelet/config.yaml` | KubeletConfiguration: `staticPodPath`, `clusterDNS`, `authentication.x509.clientCAFile`, eviction chegaralari, cgroup driver |
| `/etc/kubernetes/kubelet.conf` | API server bilan gaplashish uchun ishlatadigan kubeconfig - server URL’i, o’zining klient sertifikati |
| `/var/lib/kubelet/kubeadm-flags.env` | kubeadm hali ham uzatadigan bir nechta flag: runtime endpoint, pod-infra image |

```bash
grep -E "staticPodPath|clusterDNS|clientCAFile" /var/lib/kubelet/config.yaml
grep server /etc/kubernetes/kubelet.conf
```

:::exam-tip
Worker node’dagi nosozlikni bartaraf etish topshiriqlari deyarli har doim
o’sha fayllarning biriga borib taqaladi. `kubelet.conf`dagi noto’g’ri
`server:` porti, `config.yaml`dagi noto’g’ri CA yo’li yoki shunchaki
to’xtatilgan kubelet - uchala holatda ham alomat bir xil: `NotReady` node.
`journalctl -u kubelet` esa ularni bitta ekranda ajratib beradi.
:::

## NotReady va uni qanday o’qish kerak

```bash
kubectl get nodes
kubectl describe node node01 | grep -A6 Conditions
```

`KubeletNotReady` yoki `Unknown` bilan kelgan `Ready False` - API server
kubelet’dan xabar eshitishni to’xtatgani. Node’da:

```bash
systemctl status kubelet       # inactive? -> systemctl start kubelet
journalctl -u kubelet | tail -30
```

Tanib olishni o’rganadigan xabarlaringiz:

| Log nima deydi | Nimani anglatadi |
|---|---|
| `failed to load Kubelet config file ... no such file` | systemd drop-in’dagi yo’l noto’g’ri yoki config.yaml yo’q |
| `x509: certificate signed by unknown authority` / `unable to load client CA file` | config.yaml’dagi `clientCAFile` noto’g’ri |
| `dial tcp 127.0.0.1:6553: connect: connection refused` | kubelet.conf’dagi API server porti/manzili noto’g’ri |
| `failed to run Kubelet: ... cgroup driver` | kubelet va containerd cgroupfs yoki systemd bo’yicha kelisha olmayapti |
| `Error getting node ... node "node01" not found` | node nomi kubelet ro’yxatdan o’tgan nomga mos kelmaydi |

Tuzatgandan keyin: `systemctl daemon-reload && systemctl restart kubelet`.

## Kubelet’ning o’z API’si

Kubelet **10250**-portni tinglaydi. API server `kubectl logs`, `kubectl exec`
va `kubectl top` uchun aynan shu portga murojaat qiladi - shuning uchun
`kubectl get` ishlab turganda ham bu buyruqlar buzilishi mumkin (API
server’dagi noto’g’ri `--kubelet-client-*` sertifikatlari yoki control plane
bilan node orasidagi firewall).

:::warning
kubeadm klasterida kubelet’ning 10250-porti autentifikatsiya va
avtorizatsiyadan o’tkaziladi - lekin yoqilgan bo’lsa, faqat o’qish uchun
mo’ljallangan 10255-port o’tkazilmaydi. U sukut bo’yicha o’chirilgan;
shundayligicha qoldiring.
:::

## O’zingizni tekshiring

1. Nega kubelet Pod emas, systemd xizmati?
2. Node `NotReady`. Unda ishga tushiradigan uchta buyruqni tartibi bilan
   ayting.
3. `kubectl get pods` ishlaydi, lekin bitta node’dagi Pod’lar uchun
   `kubectl logs` timeout beradi. Bunda qaysi port va qaysi komponent
   ishtirok etadi?
