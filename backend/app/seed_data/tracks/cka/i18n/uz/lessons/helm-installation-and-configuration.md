## Bitta binary, server yo’q

Helm 3 - bitta klient binary. Klaster **ichiga** o’rnatiladigan hech narsa
yo’q - u API server bilan sizning kubeconfig’ingiz orqali gaplashadi va o’z
holatini release namespace’idagi Secret’lar sifatida saqlaydi. Shuning uchun
"Helm’ni o’rnatish" - bu bitta faylni PATH’ingizga qo’yish.

```bash
# loyihaning o'rnatuvchi skripti
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# yoki paket menejeri
sudo snap install helm --classic          # Ubuntu
brew install helm                         # macOS
# apt: helm.sh/docs/intro/install dan Helm repo'sini qo'shing, keyin apt-get install helm

# yoki tarball
wget https://get.helm.sh/helm-v3.15.2-linux-amd64.tar.gz
tar -zxvf helm-v3.15.2-linux-amd64.tar.gz && sudo mv linux-amd64/helm /usr/local/bin/helm

helm version
# version.BuildInfo{Version:"v3.15.2", ...}
```

## Uni klasterga yo’naltirish

Helm kubectl bilan bir xil kubeconfig va context qoidalaridan foydalanadi:

```bash
helm list                                  # joriy context, joriy namespace
helm list -A                               # barcha namespace'lar
helm --kube-context prod list
helm --kubeconfig /path/config -n payroll list
KUBECONFIG=/path/config helm list
```

`kubectl get pods` qayerga yo’naltirilgan bo’lsa, `helm` ham o’sha yerga
yo’naltirilgan. Release har doim **namespace ichida** bo’ladi (`-n`, sukut
bo’yicha `default`) va Helm’ning u haqidagi yozuvi
(`sh.helm.release.v1.<name>.v<revision>` Secret’lari) o’sha yerda yashaydi.

```bash
kubectl get secrets -n default -l owner=helm
# sh.helm.release.v1.my-site.v1   helm.sh/release.v1   ...
```

## Repozitoriylarni qo’shish

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo list
helm repo update                           # indekslarni yangilash - buni install/upgrade dan oldin qiling
helm search repo nginx
helm repo remove bitnami
```

Chart’lar repo qadamisiz **OCI registry’larida** ham yashashi mumkin:

```bash
helm install my-app oci://registry.example.com/charts/my-app --version 1.2.0
```

## Shell completion va muhit

```bash
source <(helm completion bash)
helm env                                   # Helm cache, config va plaginlarini qayerda saqlaydi
# HELM_CACHE_HOME=~/.cache/helm  HELM_CONFIG_HOME=~/.config/helm  HELM_REPOSITORY_CONFIG=.../repositories.yaml
```

:::exam-tip
Imtihon klasterida Helm odatda oldindan o’rnatilgan bo’ladi; avval
`helm version` bilan tekshiring. Agar topshiriqda uni o’rnatish aytilgan
bo’lsa, `get-helm-3` skripti eng qisqa yo’l va unga faqat curl va bash
kerak. Keyin topshiriqda nomi aytilgan repozitoriyni `helm repo add` bilan
qo’shing va `helm repo update` bajaring - update’ni unutish "chart not
found" yoki "version not found" chiqishining sababi.
:::

## O’zingizni tekshiring

1. Helm 3 klasterga nimani o’rnatadi va release haqidagi yozuvni qayerda
   saqlaydi?
2. Helm va kubectl qaysi klaster bilan gaplashayotgani haqida kelishmay
   qolishi mumkinmi? Nega bunday yoki nega bunday emas?
3. Siz repo qo’shdingiz, lekin `helm install` topshiriq talab qilgan chart
   versiyasini topa olmayapti. Nimani o’tkazib yubordingiz?
