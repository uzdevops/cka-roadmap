## Mock exam 1

Two hours. Twelve tasks. Total weight 100. Do them on your own cluster (a
two-node kubeadm or kind cluster is enough; where a task needs `node01`,
use your worker's name). Verify each before moving on. Solutions are in
the next lesson - do not open it until the clock stops.

Set up first:

```bash
alias k=kubectl
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"
```

---

**1.** (4) Deploy a Pod named `nginx-pod` using the image `nginx:alpine`.

**2.** (4) Deploy a Pod named `messaging` using the image `redis:alpine`
with the label `tier=msg`.

**3.** (4) Create a Namespace named `apx-x9984574`.

**4.** (6) Get the list of nodes in JSON format and store it in the file
`/opt/outputs/nodes-z3444kd9.json`.

**5.** (8) Create a Service named `messaging-service` to expose the
`messaging` Pod within the cluster on port `6379`.

**6.** (8) Create a Deployment named `hr-web-app` using the image
`kodekloud/webapp-color` with `2` replicas.

**7.** (10) Create a static Pod named `static-busybox` on the control-plane
node that uses the `busybox` image and the command `sleep 1000`.

**8.** (6) Create a Pod in the `finance` namespace named `temp-bus` with
the image `redis:alpine`.

**9.** (12) A Pod named `orange` is failing. Fix it. (Before the mock,
create it with the manifest below - the bug is intentional.)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: orange
spec:
  initContainers:
  - name: init-myservice
    image: busybox
    command: ['sh', '-c', 'sleeeep 2;']
  containers:
  - name: orange-container
    image: busybox:1.28
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
```

**10.** (10) Expose the `hr-web-app` Deployment as a Service named
`hr-web-app-service`, type `NodePort`, application port `8080`, node port
`30082`.

**11.** (8) Use JSONPath to retrieve the `osImage` of every node and store
it in `/opt/outputs/nodes_os_x43kj56.txt`.

**12.** (10) Create a PersistentVolume named `pv-analytics`: storage
`100Mi`, access mode `ReadWriteMany`, host path `/pv/data-analytics`.

**13.** (10) A Deployment named `web-front` in the `frontend` namespace
is rolling out a new image and its Pods are stuck. Roll it back to the
previous working revision and confirm all replicas are Available. (Before
the mock: `kubectl create ns frontend; kubectl create deploy web-front
--image=nginx:1.25 -n frontend --replicas=3; kubectl set image deploy
web-front nginx=nginx:1.99-doesnotexist -n frontend`.)

---

When done: score yourself per task, weights as shown, full credit only for
the exact end state. Then the solutions lesson.

:::exam-tip
Five of these thirteen tasks are one imperative command. If any of them
took you more than ninety seconds, the speed-drills lesson is where your
next hour goes.
:::

## Check yourself

1. Which tasks did you skip on first pass, and did you come back to them?
2. For each task you completed, what command did you run to **verify** it?
3. Which task took longest, and was that a knowledge, navigation or speed
   gap?
