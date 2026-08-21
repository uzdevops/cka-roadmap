## Patching a list

Containers, env vars, ports, volumes, volumeMounts, tolerations - the parts
of a spec that are lists need one more idea: **how to say which element**.
JSON 6902 uses the **index**; strategic merge uses the element's **merge
key** (`name`, for most of them).

Starting point:

```yaml
spec:
  template:
    spec:
      containers:
        - name: api
          image: myapi:1.0
          env:
            - name: MODE
              value: dev
```

## Replace an element's field

```yaml
# JSON 6902: by index
- op: replace
  path: /spec/template/spec/containers/0/image
  value: myapi:2.0
```

```yaml
# strategic merge: by name
spec:
  template:
    spec:
      containers:
        - name: api              # the merge key - which container
          image: myapi:2.0
```

The strategic form is robust to reordering; the index form breaks if a
container is added before it. Prefer names.

## Add an element

```yaml
# JSON 6902: append with `-`, or insert at an index
- op: add
  path: /spec/template/spec/containers/-
  value:
    name: sidecar
    image: fluent-bit:2.2
- op: add
  path: /spec/template/spec/containers/0/env/-
  value: {name: DEBUG, value: "true"}
```

```yaml
# strategic merge: list a new name and it is appended
spec:
  template:
    spec:
      containers:
        - name: sidecar
          image: fluent-bit:2.2
```

Because containers merge on `name`, a container whose name is not in the
original is **added**; one whose name matches is **merged**. The same goes
for env vars, ports, volumes.

## Remove an element

```yaml
# JSON 6902: by index - the only clean way
- op: remove
  path: /spec/template/spec/containers/1
```

```yaml
# strategic merge: the delete directive
spec:
  template:
    spec:
      containers:
        - name: sidecar
          $patch: delete
```

`$patch: delete` next to the merge key removes that element. It is the one
strategic-merge directive worth memorising.

## Replace a whole list

```yaml
# strategic merge: the replace directive as a list element replaces the WHOLE list
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - $patch: replace
            - name: MODE
              value: prod
```

Without the `- $patch: replace` element, `MODE` would be merged into the
existing env list and any other variables kept. With it, the list becomes
exactly what the patch says. For "replace the whole list, do not merge",
JSON 6902 says the same thing without a directive:

```yaml
- op: replace
  path: /spec/template/spec/containers/0/env
  value:
    - name: MODE
      value: prod
```

## Lists without merge keys

Some lists are plain strings (`args`, `command`, `finalizers`). They have no
merge key, so a strategic merge **replaces** the whole list; JSON 6902
addresses elements by index:

```yaml
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --verbose
- op: replace
  path: /spec/template/spec/containers/0/command
  value: ["python", "server.py", "--port", "8080"]
```

:::exam-tip
Rules of thumb for lists: **change or add a named element** → strategic
merge by `name`; **remove an element** → JSON 6902 `remove` by index (count
from 0, check the order in `kubectl kustomize` output first) or `$patch:
delete`; **plain-string lists** → JSON 6902. Always confirm with `kubectl
kustomize | grep -A<n> containers:` - index mistakes are silent until you
look.
:::

## Check yourself

1. Write the strategic merge patch that adds a sidecar container `log`
   (image `fluent-bit:2.2`) to Deployment `api`.
2. How do you remove the second container with JSON 6902, and with a
   strategic merge?
3. Why does a strategic merge replace an `args` list instead of merging it?
