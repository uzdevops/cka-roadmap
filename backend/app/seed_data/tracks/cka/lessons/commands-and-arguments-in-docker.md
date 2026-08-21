## Why a container stops when its process stops

A container is not a VM. It does not "boot" and stay up - it runs **one
process**, and when that process exits, the container exits. Run
`docker run ubuntu` and it stops immediately, because Ubuntu's default
command is `bash`, bash finds no terminal attached, and exits. That is why
every image needs to say what its process is.

```dockerfile
FROM ubuntu
CMD sleep 5
```

```bash
docker build -t ubuntu-sleeper .
docker run ubuntu-sleeper            # sleeps 5 seconds, exits
docker run ubuntu-sleeper sleep 10   # the argument REPLACES the CMD entirely
```

## CMD vs ENTRYPOINT

Two instructions decide what runs; the difference is what happens to
arguments you pass on the command line.

| Instruction | On `docker run image` | On `docker run image X` |
|---|---|---|
| `CMD ["sleep", "5"]` | runs `sleep 5` | runs `X` - **CMD is replaced** |
| `ENTRYPOINT ["sleep"]` | runs `sleep` (and fails, no argument) | runs `sleep X` - **X is appended** |
| `ENTRYPOINT ["sleep"]` + `CMD ["5"]` | runs `sleep 5` | runs `sleep X` - CMD is the *default* argument |

```dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
CMD ["5"]
```

```bash
docker run ubuntu-sleeper         # sleep 5
docker run ubuntu-sleeper 10      # sleep 10
docker run --entrypoint sleep2.0 ubuntu-sleeper 10    # sleep2.0 10 - overriding the ENTRYPOINT itself
```

That pattern - `ENTRYPOINT` is the program, `CMD` is its default arguments -
is the one most well-built images use, and it is the one Kubernetes' two
fields map onto.

## Shell form vs exec form

```dockerfile
CMD sleep 5                  # shell form: actually runs  /bin/sh -c "sleep 5"
CMD ["sleep", "5"]           # exec form: runs  sleep 5  directly
```

Exec form (the JSON array) is what you want: the process is PID 1, it
receives signals (so `docker stop` and Kubernetes' SIGTERM reach it), and no
shell is needed in the image. Shell form wraps the command in `sh -c`, which
swallows signals and makes graceful shutdown unreliable.

:::warning
`ENTRYPOINT ["sleep", "5"]` and `ENTRYPOINT sleep 5` are not the same thing.
The shell form ignores `CMD` and appended arguments entirely, because `sh -c
"sleep 5"` is already a complete command. If arguments "do nothing", check
which form the Dockerfile used.
:::

## Seeing what an image will run

```bash
docker inspect ubuntu-sleeper --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'
# [sleep] [5]
crictl inspecti nginx:1.27 | grep -A3 -i entrypoint     # on a Kubernetes node without docker
```

When a Kubernetes task hands you an image and asks you to "run it with
argument --color=green", this is how you find out whether `--color=green` is
an argument to an ENTRYPOINT (then it goes in `args`) or the whole command
(then it goes in `command`). The next lesson makes that mapping exact.

## Check yourself

1. An image has `CMD ["sleep", "5"]`. What runs for `docker run image sleep
   10`, and why?
2. An image has `ENTRYPOINT ["sleep"]` and `CMD ["5"]`. What runs for `docker
   run image 10`, and for `docker run image`?
3. Why is `CMD ["nginx", "-g", "daemon off;"]` better than `CMD nginx -g
   "daemon off;"` for a container that should stop cleanly?
