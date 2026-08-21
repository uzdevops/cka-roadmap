## A block device over the network

NFS shares a **filesystem**: the server owns it, many clients see the same
files. NBD (Network Block Device) shares a **raw block device**: the
client sees `/dev/nbd0` as if a disk were plugged in, partitions it,
formats it, and owns the filesystem entirely.

| | NFS | NBD |
|---|---|---|
| exports | a directory tree | raw blocks |
| the filesystem lives | on the server | **on the client** |
| concurrent clients | many, safely | **one at a time** (unless a cluster filesystem is used) |
| file locking, permissions | handled by NFS | ordinary local semantics |
| typical use | shared home directories, shared content | a disk for one machine: VMs, diskless boot, remote storage |

The one-writer rule is the thing to remember: two clients mounting the same
NBD export with ext4 will corrupt it, because each caches metadata believing
it is the only writer. (iSCSI is the enterprise equivalent of the same idea.)

## The server

```bash
sudo apt install nbd-server        # Debian/Ubuntu
sudo dnf install nbd               # RHEL
```

Back it with a file or a real device:

```bash
sudo mkdir -p /srv/nbd
sudo truncate -s 2G /srv/nbd/export1.img        # a sparse 2 GiB backing file
# or use a partition/LV directly: /dev/vg0/nbdvol
```

```bash
sudo vi /etc/nbd-server/config
```

```ini
[generic]
    user = nbd
    group = nbd
    includedir = /etc/nbd-server/conf.d

[export1]
    exportname = /srv/nbd/export1.img
    readonly = false
    flush = true
    fua = true
    listenaddr = 192.168.1.10

[data]
    exportname = /dev/vg0/nbdvol
    readonly = true
```

```bash
sudo systemctl enable --now nbd-server
sudo systemctl status nbd-server
sudo ss -tulpn | grep 10809           # the default NBD port
sudo ufw allow from 192.168.1.0/24 to any port 10809 proto tcp
```

## The client

```bash
sudo apt install nbd-client
sudo modprobe nbd                      # the kernel module provides /dev/nbd*
lsmod | grep nbd
ls /dev/nbd*
```

```bash
sudo nbd-client 192.168.1.10 10809 /dev/nbd0 -N export1
# Negotiation: ..size = 2048MB
# bs=512, sz=2147483648 bytes
lsblk /dev/nbd0
```

From here it is an ordinary disk:

```bash
sudo mkfs.ext4 -L nbdvol /dev/nbd0        # only the FIRST time
sudo mkdir -p /mnt/nbd
sudo mount /dev/nbd0 /mnt/nbd
df -h /mnt/nbd
echo hello | sudo tee /mnt/nbd/test.txt
```

Disconnecting - **in this order**:

```bash
sudo umount /mnt/nbd
sudo nbd-client -d /dev/nbd0
lsblk | grep nbd
```

Unmount before disconnecting, always. Pulling the device from under a
mounted filesystem is the same as yanking a disk.

## Persisting the client side

```bash
sudo vi /etc/nbdtab
```

```
# device  host          export    options
nbd0      192.168.1.10  export1   persist
```

```bash
sudo systemctl enable --now nbd-client
# fstab, with the network and device waits:
# /dev/nbd0  /mnt/nbd  ext4  _netdev,nofail,x-systemd.device-timeout=10  0  0
sudo mount -a
```

`_netdev` and `nofail` are not optional here: the device does not exist
until the network is up and `nbd-client` has connected, and a boot that
waits for it forever ends in emergency mode.

## Modes and options

```bash
sudo nbd-client 192.168.1.10 10809 /dev/nbd0 -N export1 -persist   # reconnect automatically
sudo nbd-client -N ro-export 192.168.1.10 /dev/nbd1                 # a read-only export
sudo nbd-client -l 192.168.1.10                                     # LIST the exports a server offers
sudo nbd-client -c /dev/nbd0                                        # is this device connected?
```

`readonly = true` on the server side lets many clients mount the same
export safely - the only multi-client case that is not dangerous.

## Diagnosing

```bash
# server
sudo systemctl status nbd-server; sudo journalctl -u nbd-server -n 30
sudo ss -tulpn | grep 10809
ls -l /srv/nbd/

# client
lsmod | grep nbd || sudo modprobe nbd
sudo nbd-client -l <server>
dmesg | tail -20                       # the kernel logs NBD connection events
lsblk; sudo blkid /dev/nbd0
```

| Symptom | Cause |
|---|---|
| `Error: Read failed` / negotiation fails | wrong export name (`-N`), server not running, firewall |
| `/dev/nbd0: No such device` | `modprobe nbd` not done; add `nbd` to `/etc/modules-load.d/` |
| filesystem corrupt after a second client mounted it | the one-writer rule was broken |
| device disappears, I/O errors | network interruption without `-persist` |
| boot hangs | fstab missing `_netdev`/`nofail` |

:::warning
NBD has **no authentication and no encryption** by default: anyone who can
reach port 10809 can read and write the export. Restrict it to a trusted
network with the firewall, bind it to an internal address, or tunnel it
over SSH/WireGuard. Never expose it to the internet.
:::

:::exam-tip
The likely task: export a file or device with nbd-server, connect it from
a client with `nbd-client host port /dev/nbd0 -N name`, format and mount
it. Remember `modprobe nbd` on the client, the disconnect order (umount,
then `nbd-client -d`), and that the **client** owns the filesystem - so
`mkfs` runs there, not on the server.
:::

## Check yourself

1. What is the essential difference between what NFS and NBD export, and
   where does the filesystem live in each?
2. Why must only one client mount a writable NBD export at a time?
3. What are the two commands, in order, to safely disconnect an NBD device
   that is mounted?
