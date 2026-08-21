## Where Docker keeps things

```bash
ls /var/lib/docker
# containers  image  overlay2  volumes  network  plugins  ...
```

Everything Docker stores lives under `/var/lib/docker`: image layers in
`image/` and `overlay2/`, container writable layers in `containers/`, named
volumes in `volumes/`. Kubernetes nodes running containerd have the
equivalent under `/var/lib/containerd` and `/run/containerd`; the concepts
are identical, and the CSI lessons that follow build on them.

## Images are layers

```dockerfile
FROM ubuntu               # layer 1: base filesystem
RUN apt-get update && apt-get install -y python3   # layer 2: packages
COPY app.py /app/         # layer 3: your code
ENTRYPOINT ["python3", "/app/app.py"]              # layer 4: metadata only
```

Each instruction adds a **read-only layer** containing only what changed.
Layers are content-addressed and shared: a second image `FROM ubuntu` on the
same host reuses layer 1 from disk and cache. That is why a rebuild after
changing only `app.py` is fast - layers 1-2 are cached - and why ordering
Dockerfiles "slow-changing first, fast-changing last" matters.

## The container layer

When a container starts, Docker stacks a **thin writable layer** on top of
the image's read-only layers. Everything the process writes - log files,
temp files, a modified config - goes there. Two consequences:

- The image is never modified. Two containers from one image each get their
  own writable layer.
- **The writable layer dies with the container.** `docker rm` and the data
  is gone. Writing a file into an image's path at run time is
  **copy-on-write**: the file is copied up into the writable layer, the
  image's copy is untouched.

This is the reason "my container lost its data when it restarted" is not a
bug, and the reason volumes exist.

## Volumes and bind mounts

Two ways to put persistent storage into a container:

```bash
docker volume create data_volume
docker run -v data_volume:/var/lib/mysql mysql            # VOLUME mount: Docker-managed dir under /var/lib/docker/volumes
docker run -v /data/mysql:/var/lib/mysql mysql            # BIND mount: any host path
docker run --mount type=bind,source=/data/mysql,target=/var/lib/mysql mysql   # the explicit form of the same
```

| | Volume mount | Bind mount |
|---|---|---|
| where on the host | `/var/lib/docker/volumes/<name>/_data` | wherever you say |
| managed by | Docker (`docker volume ls/rm/inspect`) | you |
| portable across hosts | no more than a bind mount - it is still local disk | no |

Both survive the container. Neither survives the host, which is the problem
the Kubernetes persistent volume model addresses.

## Storage drivers

The layering itself - stacking read-only layers and a writable one into a
single filesystem view - is the job of the **storage driver**: `overlay2` on
modern Linux, historically `aufs`, `devicemapper`, `btrfs`, `zfs`. The
driver is chosen per host and you rarely think about it; but the layered
design it implements is what makes image pulls incremental and container
starts instant.

```bash
docker info | grep "Storage Driver"
# Storage Driver: overlay2
```

:::tip
Storage drivers handle **image layers**; volume drivers (next lesson) handle
**volumes**. Same word "driver", two different plugin points - keep them
apart and the CSI lesson after will make sense.
:::

## Why this is in a Kubernetes course

Everything above maps directly:

| Docker | Kubernetes |
|---|---|
| image layers, storage driver | the same, inside containerd on every node |
| container writable layer | the same: lost when the container restarts |
| `-v name:/path` volume | `emptyDir` (per Pod) / `hostPath` (a node directory) |
| volume drivers | the CSI and PersistentVolumes |

The `Pod deleted, data gone` surprise is the Docker one wearing a Kubernetes
hat; the next lessons are the ways out.

## Check yourself

1. What happens to a file written to `/var/log/app.log` inside a container
   when the container is removed - and why?
2. What is the difference between a volume mount and a bind mount?
3. Two images both start `FROM ubuntu`. How many copies of the Ubuntu layer
   are on disk, and why does that matter for rebuilds?
