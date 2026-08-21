## Klasterga yetishning ikki yo’li

Pipeline Kubernetes’ga yo **push** qilib (job hisob ma’lumotlari bilan
`kubectl`/`helm` ishlatadi), yo **pull** qilib (klasterdagi agent repo’ni
kuzatadi - Flux/Argo CD bilan GitOps, bu yo’nalish doirasidan tashqari)
deploy qiladi. GitLab’ning push yo’lida ikki xil ta’m bor.

## A: File variable sifatida kubeconfig (tez, aniq)

```yaml
deploy-staging:
  stage: deploy
  image: bitnami/kubectl:1.30
  environment: { name: staging, url: https://staging.xyz.example.com }
  variables:
    KUBECONFIG: "$KUBECONFIG_FILE"          # File turidagi variable: yo’l
    IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
  script:
    - kubectl config current-context
    - kubectl -n xyz set image deployment/nodejs-app app="$IMAGE"
    - kubectl -n xyz rollout status deployment/nodejs-app --timeout=120s
```

Hamma joyda ishlaydi, runner’dan yetib boriladigan klaster kerak va hisob
ma’lumotini variable’ga qo’yadi - uni environment’ga scope’lang, himoya
qiling va admin kubeconfig o’rniga qisqa umrli service-account token’ini
afzal ko’ring.

## B: Kubernetes uchun GitLab agent (tavsiya etiladi)

**Agent** (`agentk`) klaster *ichida* ishlaydi va GitLab’ga chiquvchi
ulanishni saqlaydi; pipeline’lar keyin klasterga GitLab orqali, kiruvchi
firewall teshigi va sizib chiqadigan kubeconfig’siz yetadi.

1. Klaster config repo’sida: `.gitlab/agents/<name>/config.yaml`
   ```yaml
   ci_access:
     projects:
       - id: xyz-team/nodejs-app        # qaysi loyihalar pipeline’lari bu agent’ni ishlata oladi
   ```
2. *Operate → Kubernetes clusters → Connect a cluster (agent)* - token bilan
   `agentk`ni deploy qiladigan `helm upgrade --install` buyrug’ini beradi.
3. Ilova pipeline’ida agent context’ini tanlang va deploy qiling:

```yaml
deploy-staging:
  image: bitnami/kubectl:1.30
  environment: { name: staging, url: https://staging.xyz.example.com }
  script:
    - kubectl config use-context xyz-team/infra:staging-agent     # <project>:<agent name>
    - kubectl -n xyz set image deployment/nodejs-app app="$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
    - kubectl -n xyz rollout status deployment/nodejs-app
```

`KUBECONFIG`ni agent’ga kirish huquqi bor job’lar uchun GitLab kiritadi; siz
yozadigan yagona narsa `use-context`.

## `set image` o’rniga Helm

```yaml
deploy-staging:
  image: alpine/helm:3.15
  script:
    - kubectl config use-context xyz-team/infra:staging-agent
    - helm upgrade --install nodejs-app ./chart
        --namespace xyz --create-namespace
        --set image.repository="$CI_REGISTRY_IMAGE"
        --set image.tag="$CI_COMMIT_SHORT_SHA"
        --wait --timeout 3m
```

`--wait` job exit kodini "pod’lar tayyor" degan ma’noga keltiradi - bitta
flag’dagi deploy-vaqt health check. Rollback tugmasi uchun
`environment:url` va `kubectl rollout undo` (yoki `helm rollback`) bilan
juftlang.

## GitLab registry’dan image tortish

Klasterga `registry.gitlab.com/...`ni tortish uchun hisob ma’lumotlari
kerak. **Deploy token** (*Settings → Repository → Deploy tokens*,
read_registry) va pull secret yarating:

```bash
kubectl -n xyz create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com --docker-username=<token user> --docker-password=<token> \
  --docker-email=ci@xyz.example.com
# keyin Deployment’da imagePullSecrets: [{name: gitlab-registry}]
```

## O’z-o’zini tekshirish

- Kubeconfig variable’ga nisbatan agent pipeline’dan nimani olib tashlaydi?
- Agent ishlatganda job’dagi qaysi qator klasterni tanlaydi?
- Nega shunchaki `apply` emas, `helm --wait` / `kubectl rollout status`?
