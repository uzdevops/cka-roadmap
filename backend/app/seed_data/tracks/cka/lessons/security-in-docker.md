## A container is a process on the host

Before Kubernetes' security contexts make sense you need one fact straight:
a container is not a virtual machine. It is a process (or a few) on the host
kernel, wrapped in **namespaces** (so it sees its own PIDs, network, mounts,
hostname) and **cgroups** (so it is limited in CPU and memory). The kernel is
shared. The isolation is what the kernel enforces, no more.

```bash
docker run -d --name sleeper ubuntu sleep 3600
ps -ef | grep "sleep 3600"             # on the HOST: the same process, visible, PID 4023
docker exec sleeper ps -ef             # inside: it is PID 1
```

Same process, two views. Which means: what user the process runs as, and what
privileges it has, are questions about the **host**.

## Users

By default a container's process runs as **root** (UID 0) - root inside the
container *and* UID 0 on the host. Two things limit the damage:

1. The image can pick a user: `USER 1000` in the Dockerfile, or `--user` at
   run time.

```bash
docker run --user=1000 ubuntu sleep 3600
ps -ef | grep "sleep 3600"       # 1000  ...  sleep 3600
```

2. Even as root, the container's process does **not** get all of root's
   powers. Linux splits root into **capabilities**, and Docker gives a
   container only a small default set.

## Capabilities

```bash
# a default container cannot:
docker run ubuntu date -s "1 JAN 2030"        # clock_settime: Operation not permitted  (needs SYS_TIME)
docker run ubuntu reboot                      # needs SYS_BOOT
```

| Capability | Lets a process |
|---|---|
| `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETUID`, `SETGID`, `NET_BIND_SERVICE`, `KILL`, ... | the default set - enough to run a web server as root |
| `SYS_TIME` | set the clock |
| `NET_ADMIN` | change interfaces, routes, iptables |
| `SYS_ADMIN` | a grab-bag of mount and namespace operations - nearly root |
| `SYS_PTRACE` | trace other processes |

```bash
docker run --cap-add SYS_TIME ubuntu date -s "1 JAN 2030"    # works
docker run --cap-drop KILL ubuntu ...                         # take one away
docker run --privileged ubuntu ...                            # ALL capabilities + device access: a root shell on the host in all but name
```

`--privileged` is what a CNI or storage plugin sometimes needs and what no
application should have. Kubernetes exposes exactly these knobs - `runAsUser`,
`capabilities.add/drop`, `privileged` - under `securityContext`, which is the
next lesson.

## The other defaults worth knowing

- The root filesystem is writable; `--read-only` makes it not.
- Filesystem access is limited to the container's own layers plus what you
  mount; a mount of the host's `/` or of the Docker socket is an escape
  hatch.
- No host network (`--network host` changes that), no host PID namespace
  (`--pid host` changes that). Kubernetes has `hostNetwork` and `hostPID` for
  the same two.
- A **seccomp** profile filters which syscalls are allowed; **AppArmor** or
  **SELinux** label what files and capabilities the process may touch. Both
  are CKS territory; CKA needs only the user/capability/privileged trio.

:::tip
The mental model that carries over: *root in the container is root on the
host, minus capabilities.* Every Kubernetes security setting is about giving
back fewer of them, or running as not-root in the first place.
:::

## Check yourself

1. Is a container's PID 1 visible on the host? As what?
2. A container running as root tries to set the system clock and is refused.
   Why, and what would allow it?
3. What does `--privileged` grant, and why is it different from `--cap-add
   SYS_ADMIN`?
