## Containers on a Linux host

A container is a process on **your** kernel, isolated with namespaces
(its own view of processes, network, mounts, users) and limited with
cgroups (CPU, memory). No guest kernel, no boot - which is why it starts
in milliseconds where a VM takes seconds.

Two runtimes appear in the objectives: **docker** and **podman**. The
commands are deliberately identical; podman is daemonless and can run
rootless, and on RHEL it is the default.

```bash
sudo apt install docker.io      # or: sudo dnf install podman
sudo systemctl enable --now docker
docker version; podman version
alias docker=podman             # every command below works with either
```

## Images and containers

An **image** is a read-only filesystem plus metadata; a **container** is a
running (or stopped) instance of one, with a writable layer on top.

```bash
docker pull nginx:1.27-alpine        # fetch an image (always pin a tag, never rely on :latest)
docker images                        # local images
docker search nginx
docker rmi nginx:1.27-alpine         # remove an image
docker image prune -a                # remove unused images
```

## Running

```bash
docker run -d --name web -p 8080:80 nginx:1.27-alpine
#   -d detached      --name a stable name      -p HOSTPORT:CONTAINERPORT
docker run -it --rm alpine:3.20 sh          # interactive, delete on exit
docker run -d --name db \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  --restart=unless-stopped \
  --memory=512m --cpus=1 \
  postgres:16
docker run --rm -v /srv/data:/data:ro alpine ls /data      # bind mount, read-only
```

| Flag | Does |
|---|---|
| `-d` | background |
| `-it` | interactive terminal |
| `--rm` | delete the container when it exits |
| `--name` | a name instead of a random one |
| `-p 8080:80` | publish host port → container port |
| `-e K=V` | environment variable |
| `-v name:/path` | **named volume** (managed, persists) |
| `-v /host:/path` | **bind mount** (a host directory); add `:ro` for read-only |
| `--restart` | `no`, `on-failure`, `always`, `unless-stopped` |
| `--memory`, `--cpus` | limits (cgroups) |
| `--network` | which network to join |
| `-u 1000:1000` | run as a uid instead of root |

## Managing

```bash
docker ps                       # running
docker ps -a                    # including stopped
docker logs web; docker logs -f --tail 50 web
docker exec -it web sh          # a shell inside a RUNNING container
docker exec web nginx -t
docker stop web; docker start web; docker restart web
docker rm web                   # remove a stopped container; -f forces
docker inspect web | less       # everything: IP, mounts, env, state
docker stats                    # live CPU/memory per container
docker top web
docker cp web:/etc/nginx/nginx.conf ./        # copy files in or out
docker port web
docker system df; docker system prune         # what is using disk; clean up
```

## Data: volumes vs bind mounts

The container's writable layer disappears with the container. Anything
that must survive goes in a volume.

```bash
docker volume create pgdata
docker volume ls; docker volume inspect pgdata
docker run -d -v pgdata:/var/lib/postgresql/data postgres:16     # named volume: docker manages the location
docker run -d -v /srv/www:/usr/share/nginx/html:ro nginx         # bind mount: you choose the path
docker volume rm pgdata
```

Named volumes for databases and application state; bind mounts for config
files and content you edit on the host.

## Networking

```bash
docker network ls                                   # bridge, host, none
docker network create appnet
docker run -d --name db --network appnet postgres:16
docker run -d --name api --network appnet -p 8080:8080 myapi     # reaches the db as "db"
docker network inspect appnet
```

On a user-defined network, containers resolve each other **by name** - the
reason to create one instead of using the default bridge.

## Building an image

```dockerfile
FROM alpine:3.20
RUN apk add --no-cache python3
WORKDIR /app
COPY app.py .
EXPOSE 8000
USER 1000
CMD ["python3", "app.py"]
```

```bash
docker build -t myapp:1.0 .
docker run -d -p 8000:8000 myapp:1.0
docker tag myapp:1.0 registry.example.com/myapp:1.0
docker push registry.example.com/myapp:1.0
docker save myapp:1.0 | gzip > myapp.tar.gz         # move an image without a registry
docker load < myapp.tar.gz
```

## Containers as services

```bash
# podman: generate a systemd unit for a running container
podman generate systemd --new --name web > /etc/systemd/system/container-web.service
sudo systemctl daemon-reload && sudo systemctl enable --now container-web
# docker: use --restart=unless-stopped, or a unit with ExecStart=/usr/bin/docker start -a web
```

Rootless podman (`podman` as a normal user, containers in your own user
namespace) is the security-relevant difference from docker's root daemon;
`podman info | grep rootless` tells you which you are in.

:::warning
`-v /:/host` or `--privileged` or adding a user to the `docker` group all
amount to giving root: the docker daemon runs as root and will mount
anything you ask. Treat `docker` group membership as sudo without a
password, and prefer rootless podman where it fits.
:::

:::exam-tip
Expect: "run image X as a container named Y, publishing port A to B, with
volume V mounted at /path, and make sure it restarts automatically". That
is one `docker run -d --name Y -p A:B -v V:/path --restart=unless-stopped
X`. Verify with `docker ps`, `docker inspect`, and `curl localhost:A`.
:::

## Check yourself

1. What is the difference between an image and a container, and between a
   named volume and a bind mount?
2. Which flag publishes a port, and in which order are host and container
   ports written?
3. Why do containers on a user-defined network resolve each other by name
   when those on the default bridge do not?
