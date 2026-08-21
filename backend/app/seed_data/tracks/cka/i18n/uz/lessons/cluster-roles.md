## Namespace’ga sig’maydigan ruxsatlar

Ba’zi resurslar hech qaysi namespace’da bo’lmaydi - node’lar,
PersistentVolume’lar, StorageClass’lar, Namespace’larning o’zi,
ClusterRole’lar, CSR’lar. Role ular haqida hech narsa bera olmaydi, chunki
Role namespace ichida yashaydi, ular esa yo’q. **ClusterRole** va
**ClusterRoleBinding** juftligi - buning klaster darajasidagi varianti.

```bash
kubectl api-resources --namespaced=false        # ClusterRole talab qiladigan narsalar
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-admin                # namespace yo'q
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: michelle-node-admin
subjects:
  - kind: User
    name: michelle
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-admin
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl create clusterrole node-admin --verb=get,list,watch,create,delete --resource=nodes
kubectl create clusterrolebinding michelle-node-admin --clusterrole=node-admin --user=michelle
kubectl auth can-i list nodes --as michelle                    # yes

kubectl create clusterrole storage-admin --verb='*' --resource=persistentvolumes,storageclasses
kubectl create clusterrolebinding michelle-storage-admin --clusterrole=storage-admin --user=michelle
```

## ClusterRole namespace’li resurslar uchun ham

ClusterRole namespace’li resurslarni ham nomlashi mumkin - `pods`,
`deployments`. **ClusterRoleBinding** bilan bog’lansa, u bularni **har bir**
namespace’da beradi; `dev` namespace’dagi **RoleBinding** bilan bog’lansa,
faqat `dev`da beradi.

| Role turi | Binding turi | Amaldagi qamrov |
|---|---|---|
| Role | RoleBinding | bitta namespace (Role’niki) |
| ClusterRole | RoleBinding | bitta namespace (binding’niki) |
| ClusterRole | ClusterRoleBinding | har bir namespace + klaster darajasidagi resurslar |
| Role | ClusterRoleBinding | **ruxsat etilmagan** |

Yodda tutish kerak bo’lgani - o’rtadagi qator: bir marta aniqlang, har bir
namespace uchun alohida bog’lang.

```bash
kubectl create rolebinding ana-edit -n dev --clusterrole=edit --user=ana
```

## O’rnatilganlari

```bash
kubectl get clusterroles | head -40
kubectl describe clusterrole view
```

| ClusterRole | Nima uchun mo’ljallangan |
|---|---|
| `cluster-admin` | hamma joyda hamma narsa; sukut bo’yicha `system:masters` guruhiga bog’langan |
| `admin` | namespace ichida to’liq nazorat, o’sha yerdagi RBAC bilan birga (RoleBinding orqali) |
| `edit` | namespace’dagi obyektlarning ko’pini o’qish/yozish; RBAC emas |
| `view` | namespace’da faqat o’qish; Secret’larni o’qiy olmaydi |
| `system:*` | komponentlar uchun - `system:kube-scheduler`, `system:node`, `system:kube-controller-manager` ... |

O’zingiznikini yozishdan oldin o’rnatilganlarini bog’lang: "ana’ga dev
namespace’ida faqat o’qish huquqini bering" - bu
`rolebinding ... --clusterrole=view`, bitta qator, va uni loyihaning o’zi
qo’llab-quvvatlaydi.

:::exam-tip
Savol qamrovni odatda o’z otlari bilan aytadi: **nodes**,
**persistentvolumes**, **storageclasses**, **namespaces** → ClusterRole +
ClusterRoleBinding. **pods**, **deployments** va "X namespace’da" → Role +
RoleBinding (yoki ClusterRole + RoleBinding). "barcha namespace’larda" →
ClusterRole + ClusterRoleBinding. Ularni chalkashtirsangiz, mavjud bo’lgan,
lekin hech narsa bermaydigan binding chiqadi.
:::

## Agregatsiyalangan ClusterRole’lar

`view`, `edit` va `admin` - **agregatsiyalangan**: controller manager ularni
qo’shilishi kerakligi label bilan belgilangan har bir ClusterRole’dan yig’adi.
CRD muallifi o’rnatilgan rolni tahrirlamasdan `view`ga o’zining yangi
resursini ko’rsatishi aynan shu tarzda bo’ladi:

```yaml
metadata:
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
```

Imtihonda bunday narsa yozmaysiz; `describe clusterrole view` qilib, qoidalar
qayerdan kelayotganiga hayron bo’lganingizda shu label’ni ko’rasiz.

## Klaster bo’ylab berilgan ruxsatlarni o’qish

```bash
kubectl get clusterrolebindings -o wide | grep michelle
kubectl describe clusterrolebinding cluster-admin      # hozir kim cluster-admin - bitta qatorda xavfsizlik auditi
kubectl auth can-i --list --as michelle                # -n yo'q: klaster darajasidagi ko'rinish
```

## O’zingizni tekshiring

1. Bulardan qaysi uchtasiga ClusterRole kerak: pods, nodes, deployments,
   storageclasses, namespaces?
2. ClusterRole’ni RoleBinding bilan bog’lash nimaga erishtiradi va buni nega
   qilgan bo’lar edingiz?
3. Hozir `cluster-admin` kimda ekanini qanday aniqlaysiz?
