## Keys instead of passwords

```bash
ssh-keygen -t ed25519 -C "ahmad@laptop"            # the modern default; -t rsa -b 4096 if ed25519 is unsupported
# ~/.ssh/id_ed25519       private - NEVER leaves the machine, chmod 600
# ~/.ssh/id_ed25519.pub   public  - copy this anywhere
ssh-copy-id ahmad@server                            # appends the .pub to the server's authorized_keys
ssh-copy-id -i ~/.ssh/deploy.pub deploy@server
ssh ahmad@server                                    # no password
```

Manually, when `ssh-copy-id` is unavailable:

```bash
cat ~/.ssh/id_ed25519.pub | ssh ahmad@server 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
```

Permissions are enforced by sshd and are the most common reason keys
"don't work":

| Path | Mode |
|---|---|
| `~` | not group- or world-**writable** |
| `~/.ssh` | `700` |
| `~/.ssh/authorized_keys` | `600` |
| private keys | `600` |

```bash
chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys ~/.ssh/id_*
sudo journalctl -u ssh | grep -i "authentication refused\|bad ownership"
```

## The agent, and passphrases

```bash
ssh-keygen -t ed25519                     # give it a passphrase
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519                  # type the passphrase once per session
ssh-add -l                                 # loaded keys
ssh-add -D                                 # forget them
ssh -A user@bastion                        # agent forwarding - convenient, and a risk on untrusted hosts
```

A passphrase plus the agent gives you key security **and** convenience; a
passphrase-less key is a password lying in a file (acceptable for
automation with a restricted, dedicated key).

## Hardening sshd

```bash
sudo vi /etc/ssh/sshd_config          # or a file in /etc/ssh/sshd_config.d/
```

```
Port 22                              # or a non-default port (obscurity, not security)
PermitRootLogin no
PasswordAuthentication no            # keys only - the single biggest win
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
AllowUsers ahmad deploy              # or: AllowGroups ssh-users
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
Banner /etc/issue.net
```

```bash
sudo sshd -t                          # SYNTAX CHECK - do this before every reload
sudo sshd -T | grep -Ei "permitroot|password|port|allowusers"   # the EFFECTIVE config
sudo systemctl reload ssh             # 'sshd' on RHEL
```

:::warning
Never `systemctl restart ssh` after an untested change while it is your
only way in. Do this instead: `sshd -t`, then `reload`, then **open a
second session in a new terminal** and confirm it works before closing the
first. If the new session fails, you still have the old one to undo the
change. A `Match` block or an `AllowUsers` typo will otherwise lock you
out permanently.
:::

Per-group or per-address exceptions:

```
Match Group sftponly
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no

Match Address 192.168.1.0/24
    PasswordAuthentication yes
```

`Match` blocks must be at the **end** of the file - everything after a
`Match` belongs to it.

## The client side

```bash
vi ~/.ssh/config
```

```
Host web01
    HostName 192.168.1.50
    User ahmad
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60

Host *.internal
    User admin
    ProxyJump bastion.example.com          # hop through a bastion automatically

Host bastion.example.com
    User ahmad
    IdentityFile ~/.ssh/bastion_key
```

```bash
chmod 600 ~/.ssh/config
ssh web01                                  # all of the above, one word
```

```bash
ssh -p 2222 -i ~/.ssh/key user@host
ssh -J bastion user@internal-host          # jump host on the command line
ssh user@host 'uptime; df -h'              # run and return
ssh -t user@host 'sudo systemctl status nginx'    # -t when the remote command needs a terminal
ssh -v user@host                           # verbose: the authentication conversation - use -vvv when stuck
scp file user@host:/tmp/; rsync -av dir/ user@host:/dst/
sftp user@host
```

## Host keys

On first connection you are asked to trust the server's fingerprint; it is
stored in `~/.ssh/known_hosts`. A changed key means either a rebuilt server
or a man-in-the-middle:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub      # the server's fingerprint, checked from the console
ssh-keygen -R web01                                    # forget an old host key after a rebuild
ssh-keyscan -t ed25519 web01 >> ~/.ssh/known_hosts
```

## Tunnels

```bash
ssh -L 8080:localhost:80 user@host        # LOCAL: my :8080 → host's :80  (reach a remote service)
ssh -L 5433:db.internal:5432 user@bastion # through a bastion to a third host
ssh -R 9000:localhost:3000 user@host      # REMOTE: host's :9000 → my :3000  (expose a local service)
ssh -D 1080 user@host                     # SOCKS proxy through the host
ssh -fN -L 8080:localhost:80 user@host    # background, no shell
```

`-L` brings something remote to you; `-R` pushes something local out.
(`GatewayPorts` and `AllowTcpForwarding` on the server control whether
these are permitted.)

## Diagnosing

```bash
ssh -vvv user@host 2>&1 | grep -iE "offering|authentications|denied|permission"
sudo journalctl -u ssh -f
sudo tail -f /var/log/auth.log
sudo sshd -T | grep -i pubkeyauth
sudo ss -tulpn | grep :22
sudo lastb | head                          # failed attempts
```

| Symptom | Cause |
|---|---|
| `Permission denied (publickey)` | key not in `authorized_keys`, wrong key offered, or bad permissions on `~`, `~/.ssh`, `authorized_keys` |
| `Connection refused` | sshd not running, or the wrong port |
| `Connection timed out` | firewall or routing - not sshd |
| `Host key verification failed` | changed host key - verify it, then `ssh-keygen -R` |
| password prompt despite a key | `PasswordAuthentication yes` and the key is not being accepted - `ssh -v` shows why |
| works locally, not remotely | `ListenAddress`, firewall, or `AllowUsers` |

:::exam-tip
Very likely: "allow user X to log in with a key and disable password
authentication", or "change the SSH port to N". Sequence: edit
sshd_config (or a drop-in), `sshd -t`, `systemctl reload ssh`, and on a
non-default port also the firewall (`ufw allow N/tcp`) and, on RHEL,
SELinux (`semanage port -a -t ssh_port_t -p tcp N`). Verify from a second
session before you close the first.
:::

## Check yourself

1. Which permissions must `~/.ssh` and `authorized_keys` have, and what
   happens otherwise?
2. What is the difference between `ssh -L` and `ssh -R`?
3. You change the SSH port on a RHEL host with a firewall. Which three
   things must you change?
