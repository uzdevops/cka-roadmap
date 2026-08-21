## JSONPath on kubectl output

`kubectl get <thing> -o json` is the document; `-o jsonpath='{...}'` is the
query. Two differences from the pure language: `$` is optional (kubectl
adds it), and the query is wrapped in `{ }`.

```bash
kubectl get pod web -o json | less                          # look at the document first
kubectl get pod web -o jsonpath='{.metadata.name}'
kubectl get pod web -o jsonpath='{.spec.containers[0].image}'
kubectl get pod web -o jsonpath='{.status.podIP}'
```

## Lists of objects: .items

`kubectl get pods` with no name returns a **List** whose objects are under
`.items`. Almost every useful query starts there.

```bash
kubectl get nodes -o jsonpath='{.items[*].metadata.name}'
# controlplane node01 node02
kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}'
kubectl get nodes -o jsonpath='{.items[*].status.capacity.cpu}'
# 4 4 4
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}'      # every image in the cluster
kubectl get pv -o jsonpath='{.items[*].spec.capacity.storage}'
```

The output of `[*]` is space-separated on one line. Add newlines with
`{"\n"}` - literal strings go in double quotes inside the braces:

```bash
kubectl get nodes -o jsonpath='{.items[*].metadata.name}{"\n"}'
kubectl get nodes -o jsonpath='{.items[*].metadata.name}{"\n"}{.items[*].status.capacity.cpu}{"\n"}'
# controlplane node01 node02
# 4 4 4
```

## range: one line per item

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.cpu}{"\n"}{end}'
# controlplane    4
# node01          4
# node02          4
```

`{range list}...{end}` loops; inside it, paths are relative to the current
element. This is how you build a table by hand - and how you get a Pod →
node listing, images per Pod, and so on:

```bash
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"/"}{.metadata.name}{" → "}{.spec.nodeName}{"\n"}{end}'
```

## custom-columns: the same thing, formatted

```bash
kubectl get nodes -o custom-columns=NODE:.metadata.name,CPU:.status.capacity.cpu,ARCH:.status.nodeInfo.architecture
# NODE           CPU   ARCH
# controlplane   4     amd64
# node01         4     amd64
kubectl get pods -o custom-columns=POD:.metadata.name,IMAGE:.spec.containers[*].image,NODE:.spec.nodeName
kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage --no-headers
```

`custom-columns=HEADER:path,HEADER:path` - no braces, no `.items` (it
iterates for you), headers you choose. Pair it with `--sort-by`.

## --sort-by

```bash
kubectl get pv --sort-by=.spec.capacity.storage
kubectl get pv --sort-by=.spec.capacity.storage -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get nodes --sort-by=.status.capacity.cpu
kubectl get events --sort-by=.lastTimestamp
```

`--sort-by` takes a JSONPath (no braces, no `.items`) and sorts the normal
table output by it.

## Filters

```bash
kubectl get pods -o jsonpath='{.items[?(@.spec.nodeName=="node01")].metadata.name}'
kubectl get nodes -o jsonpath='{.items[?(@.metadata.name=="node01")].status.addresses[?(@.type=="InternalIP")].address}'
kubectl config view --kubeconfig=my-kube-config -o jsonpath='{.contexts[?(@.context.user=="aws-user")].name}'
kubectl get nodes -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}'
```

Filters are where the quoting gets delicate: single quotes around the whole
expression for the shell, double quotes for strings inside. Build them up
piece by piece and test each.

## Where JSONPath stops and jq starts

kubectl's JSONPath has no `..` recursive descent, no arithmetic, no
string functions. For anything beyond extraction, `-o json | jq`:

```bash
kubectl get pods -A -o json | jq -r '.items[] | select(.status.phase!="Running") | .metadata.namespace + "/" + .metadata.name'
kubectl get nodes -o json | jq '.items[].status.allocatable'
```

jq is usually on the exam node; `-o jsonpath` always is.

## The exam's favourite asks

| Ask | Command |
|---|---|
| node names to a file | `kubectl get nodes -o jsonpath='{.items[*].metadata.name}' > /opt/nodes.txt` |
| node OS images | `kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.osImage}'` |
| a node's InternalIP | `kubectl get node node01 -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}'` |
| PVs sorted by capacity, name+size columns | `kubectl get pv --sort-by=.spec.capacity.storage -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage` |
| the context for a user in a given kubeconfig | `kubectl config view --kubeconfig=<f> -o jsonpath='{.contexts[?(@.context.user=="<u>")].name}'` |
| images of all Pods in a namespace | `kubectl get pods -n <ns> -o jsonpath='{.items[*].spec.containers[*].image}'` |
| Pods per node | `kubectl get pods -A -o custom-columns=POD:.metadata.name,NODE:.spec.nodeName --sort-by=.spec.nodeName` |

:::exam-tip
When the task says "write the output to /opt/file", redirect the
`jsonpath` output with `>`; check with `cat` - a missing `{"\n"}` is fine,
an extra `[ ]` or a header that should not be there is not. For "sorted by"
use `--sort-by`; for "columns" use `custom-columns`; for "the value of"
use `-o jsonpath`. Always `kubectl get ... -o json | less` first if you are
unsure of the path - guessing field names costs more than ten seconds of
looking.
:::

## Check yourself

1. Write the command that prints each node's name and its InternalIP, one
   per line.
2. What does `--sort-by` take, and what is the difference between it and
   sorting in jq?
3. Write the command that lists PV names and capacities sorted by capacity.
