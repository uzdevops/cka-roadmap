## Two tiny tools for two constant chores

Switching clusters and switching namespaces are the two things you do most
and type the longest commands for:

```bash
kubectl config use-context prod-cluster
kubectl config set-context --current --namespace=payroll
```

**kubectx** and **kubens** (one project, github.com/ahmetb/kubectx) wrap
those:

```bash
kubectx                       # list contexts, current highlighted
kubectx prod-cluster          # switch
kubectx -                     # back to the previous one
kubectx dev=dev-user@cluster1 # rename a context

kubens                        # list namespaces in the current context
kubens payroll                # set the default namespace
kubens -                      # back
kubens -c                     # print the current namespace
```

They edit the same kubeconfig `kubectl config` edits - there is no extra
state, so mixing them with raw `kubectl config` is fine.

## Installing

```bash
# release binaries
sudo git clone https://github.com/ahmetb/kubectx /opt/kubectx
sudo ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx
sudo ln -s /opt/kubectx/kubens /usr/local/bin/kubens
# or: brew install kubectx / apt install kubectx (on some distros) / a kubectl krew plugin (kubectl ctx, kubectl ns)
```

With `fzf` installed they become interactive pickers.

## Why this is in a security phase

Because "which cluster am I pointed at" is a security question. The
incident that every team has had once: a destructive command meant for
staging, run in production, because the shell was still on the wrong
context. Two habits prevent it:

1. Make the context **visible** - a prompt that shows `kubectx -c` /
   `kubens -c` (kube-ps1 does this), or at least running `kubectx` before
   anything destructive.
2. Make the **credentials** different - a production context whose user has
   `view` by default, with a separate context for changes. Then the wrong
   window fails safely.

:::tip
In the exam you do not have kubectx; you have `kubectl config use-context`
and the task telling you which context. Type it at the start of every task,
every time. The habit it is standing in for is the same: know where you are
before you act.
:::

## Equivalents without installing anything

```bash
alias kctx='kubectl config use-context'
alias kns='kubectl config set-context --current --namespace'
kubectl config get-contexts          # the list
kubectl config current-context
kubectl config view --minify -o jsonpath='{..namespace}'     # the current default namespace
```

## Check yourself

1. What do `kubectx` and `kubens` actually change when you run them?
2. Why is knowing your current context a security matter?
3. What is the kubectl equivalent of `kubens payroll`?
