## Sharing a directory over the network

NFS exports a directory from a server; clients mount it as if it were
local. Unix permissions travel with the files, which is what makes NFS the
natural choice between Linux hosts (CIFS/Samba is the Windows-compatible
alternative).

## The server

```bash
sudo apt install nfs-kernel-server        # Debian/Ubuntu
sudo dnf install nfs-utils                # RHEL
sudo systemctl enable --now nfs-server    # (nfs-kernel-server on Debian)
```

```bash
sudo mkdir -p /srv/nfs/shared
sudo chown nobody:nogroup /srv/nfs/shared     # or a real owner, matching the clients' UIDs
sudo chmod 2775 /srv/nfs/shared
sudo vi /etc/exports
```

```
/srv/nfs/shared   192.168.1.0/24(rw,sync,no_subtree_check)
/srv/nfs/ro       192.168.1.0/24(ro,sync,no_subtree_check)
/srv/nfs/admin    192.168.1.10(rw,sync,no_root_squash,no_subtree_check)
/srv/nfs/home     *.example.com(rw,sync,root_squash,no_subtree_check)
```

Syntax: `directory client(options)` - **no space** between the client and
the opening parenthesis. A space means "export to everyone with default
options, and also to that client", which is a classic accidental
world-export.

| Option | Means |
|---|---|
| `rw` / `ro` | writable / read-only |
| `sync` | reply only after data is on disk (safe; the default) |
| `async` | reply early - faster, risks data loss on a crash |
| `root_squash` | **default**: remote root is mapped to `nobody` |
| `no_root_squash` | remote root **is** root here - dangerous, use only for specific admin hosts |
| `all_squash` | every remote user becomes `nobody` - good for public read-only shares |
| `anonuid=`/`anongid=` | which local identity squashed users get |
| `no_subtree_check` | recommended: fewer problems when files are renamed |
| `secure` | require a source port below 1024 (default) |

```bash
sudo exportfs -arv          # re-read /etc/exports and apply
sudo exportfs -v            # what is exported right now
sudo exportfs -u 192.168.1.0/24:/srv/nfs/shared     # unexport one
showmount -e localhost      # what clients would see
```

Firewall: NFSv4 needs only **TCP 2049**.

```bash
sudo ufw allow from 192.168.1.0/24 to any port nfs
sudo firewall-cmd --permanent --add-service=nfs && sudo firewall-cmd --reload
# NFSv3 also needs rpc-bind and mountd - pin their ports or just use v4
```

## The client

```bash
sudo apt install nfs-common          # or: dnf install nfs-utils
showmount -e 192.168.1.10             # what does the server offer?
sudo mkdir -p /mnt/shared
sudo mount -t nfs 192.168.1.10:/srv/nfs/shared /mnt/shared
df -h /mnt/shared; findmnt /mnt/shared
touch /mnt/shared/test && ls -l /mnt/shared
sudo umount /mnt/shared
```

Persistently:

```
192.168.1.10:/srv/nfs/shared  /mnt/shared  nfs  defaults,_netdev,rw  0  0
# or, better for a share that may be unavailable:
192.168.1.10:/srv/nfs/shared  /mnt/shared  nfs  rw,soft,timeo=30,retrans=3,_netdev,nofail  0  0
```

```bash
sudo mount -a
findmnt -t nfs4
```

`_netdev` waits for the network; without it the boot may try to mount
before there is an address. `nofail` keeps a missing server from blocking
the boot.

| Client option | Effect |
|---|---|
| `hard` (default) | retry **forever** if the server goes away - processes hang in `D` state but no data is lost |
| `soft` | give up after `timeo`×`retrans` - I/O errors instead of hangs; risks data loss on writes |
| `intr` | (legacy) allow signals to interrupt; modern kernels handle this |
| `timeo=`, `retrans=` | tenths of a second per attempt, and how many attempts |
| `rsize=`/`wsize=` | transfer sizes; leave to negotiation unless tuning |
| `noatime`, `nodev`, `nosuid` | as for any filesystem - `nosuid` on an NFS mount is wise |
| `vers=4.2` | pin the protocol version |

Rule of thumb: **`hard` for anything you write** (data integrity),
`soft` only for read-only or optional mounts where a hang is worse than an
error.

## Identity: whose UID?

NFS sends **numeric UIDs**. If `alice` is 1001 on the client and 1005 on
the server, files appear owned by the wrong user. Fixes: keep UIDs
consistent (LDAP, week 8), or use `all_squash` with `anonuid`, or NFSv4's
`idmapd` with matching domains.

```bash
id alice           # on both machines - they must match
ls -ln /mnt/shared # numeric owners, to see what the server really stores
```

## Diagnosing

```bash
# server
sudo systemctl status nfs-server
sudo exportfs -v
sudo ss -tulpn | grep 2049
sudo journalctl -u nfs-server -n 30

# client
showmount -e <server>            # if this fails, it is network/firewall, not NFS options
sudo mount -v -t nfs server:/path /mnt/x
nfsstat -c; nfsstat -m
findmnt -t nfs4
```

| Symptom | Cause |
|---|---|
| `access denied by server` | the client is not in `/etc/exports`, or `exportfs -ra` was not run |
| `Permission denied` writing | exported `ro`, or Unix permissions, or `root_squash` and you are root |
| `No route to host` / timeout | firewall (2049), or the server is down |
| `mount: wrong fs type` | `nfs-common`/`nfs-utils` not installed on the client |
| files owned by `nobody` | UID mismatch or NFSv4 idmap domain mismatch |
| commands hang forever on the mount | `hard` mount and the server is gone - `umount -l`, or use `soft` where appropriate |
| boot hangs | missing `_netdev`/`nofail` in fstab |

:::warning
`no_root_squash` lets a remote root write SUID binaries into the share as
root - effectively granting root on the server to anyone who can become
root on the client. Use it only for a named admin host, never with a
subnet or `*`.
:::

:::exam-tip
Both halves may be asked: export a directory with given options
(`/etc/exports` + `exportfs -arv` + firewall, verified with `showmount -e
localhost`), and mount it persistently on a client (fstab with `_netdev`,
`mount -a`, verified with `df -h`). Watch the no-space rule in
`/etc/exports` and remember `exportfs -arv` after every edit.
:::

## Check yourself

1. What does `root_squash` do, and why is `no_root_squash` dangerous?
2. What is the difference between a `hard` and a `soft` NFS mount, and
   which do you choose for writes?
3. Which two fstab options keep an NFS mount from breaking the boot?
