## Already there

Kustomize has been part of `kubectl` since 1.14:

```bash
kubectl kustomize ./overlays/prod          # render
kubectl apply -k ./overlays/prod           # render and apply
kubectl delete -k ./overlays/prod
kubectl diff -k ./overlays/prod
kubectl version --client                   # kustomize version is listed in newer kubectl
```

For most work that is all you need, and it is all the exam needs.

## The standalone binary

`kubectl`'s embedded copy lags the project by a few releases and lacks a few
flags (`--enable-helm`, `--load-restrictor`, the `edit` subcommands). The
standalone `kustomize` is the same engine, current:

```bash
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
kustomize version
```

```bash
kustomize build ./overlays/prod                    # == kubectl kustomize
kustomize build ./overlays/prod | kubectl apply -f -
kustomize edit set image myapp=myapp:2.1.0         # edits kustomization.yaml for you
kustomize edit add resource deployment.yaml
kustomize edit set namespace prod
kustomize create --autodetect                      # generate a kustomization.yaml from the files in a dir
```

The `edit` subcommands are scriptable ways to change a kustomization - the
CI idiom `kustomize edit set image app=app:$SHA && git commit` is how many
pipelines bump versions.

## Which one when

| Use | Command |
|---|---|
| render to see what you would apply | `kubectl kustomize dir/` |
| apply | `kubectl apply -k dir/` |
| need `--enable-helm`, or the newest features | `kustomize build` |
| automate edits to a kustomization | `kustomize edit ...` |

:::exam-tip
`kubectl apply -k` needs a directory **containing `kustomization.yaml`** -
not the file itself. `kubectl apply -k overlays/prod/kustomization.yaml`
fails; `kubectl apply -k overlays/prod` works. And `-k` is not `-f`: `-f` on
a kustomization.yaml tries to apply it as a Kubernetes object and errors
with "no kind Kustomization".
:::

## Check yourself

1. What do you need to install to use Kustomize with kubectl?
2. Which two commands render and apply an overlay?
3. `kubectl apply -k overlays/prod/kustomization.yaml` fails. Why?
