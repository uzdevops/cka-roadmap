## Two families, the same ideas

| | Debian/Ubuntu | RHEL/Fedora/Rocky |
|---|---|---|
| high level | `apt` | `dnf` (older: `yum`) |
| low level | `dpkg` | `rpm` |
| package | `.deb` | `.rpm` |
| repo config | `/etc/apt/sources.list`, `sources.list.d/` | `/etc/yum.repos.d/*.repo` |
| cache | `/var/cache/apt/archives/` | `/var/cache/dnf/` |
| log | `/var/log/apt/history.log` | `/var/log/dnf.log` |

The high-level tool resolves dependencies and talks to repositories; the
low-level one operates on a single file that is already on disk.

## apt: the everyday commands

```bash
sudo apt update                     # refresh the package lists - ALWAYS first
sudo apt install nginx
sudo apt install nginx=1.24.0-1     # a specific version
sudo apt install -y --no-install-recommends nginx
sudo apt remove nginx               # remove the program, KEEP config files
sudo apt purge nginx                # remove config files too
sudo apt autoremove                 # drop dependencies nothing needs any more
sudo apt upgrade                    # upgrade everything (never removes packages)
sudo apt full-upgrade               # allowed to remove things to satisfy dependencies
apt search nginx
apt show nginx                      # version, size, dependencies, description
apt list --installed | grep nginx
apt list --upgradable
apt-cache policy nginx              # installed version, candidate, and which repo it comes from
sudo apt-mark hold nginx            # pin: do not upgrade this
sudo apt-mark unhold nginx
apt-mark showhold
sudo apt clean; sudo apt autoclean  # empty the download cache
```

## dpkg: the local layer

```bash
sudo dpkg -i package.deb            # install a downloaded file (does NOT fetch dependencies)
sudo apt install -f                 # ...then fix the missing dependencies
sudo dpkg -r nginx; sudo dpkg -P nginx
dpkg -l                             # everything installed ('ii' = installed ok)
dpkg -l | grep nginx
dpkg -L nginx                       # which FILES the package installed
dpkg -S /etc/nginx/nginx.conf       # which PACKAGE owns this file
dpkg -s nginx                       # status and metadata
dpkg -c package.deb                 # contents of a file, without installing
dpkg --get-selections > pkgs.txt    # replicate a machine's package set
```

## dnf / yum

```bash
sudo dnf install nginx
sudo dnf install -y nginx-1.24.0
sudo dnf remove nginx
sudo dnf upgrade                    # everything (dnf update is the same)
sudo dnf upgrade nginx
sudo dnf search nginx
dnf info nginx
dnf list installed | grep nginx
dnf list available
sudo dnf provides /usr/sbin/nginx   # which package provides this file/command
dnf repoquery -l nginx              # its file list
sudo dnf history                    # every transaction, numbered
sudo dnf history undo 42            # ROLL BACK a transaction - dnf's best feature
sudo dnf clean all
sudo dnf group install "Development Tools"
sudo dnf install epel-release       # the common extra repo
```

## rpm: the local layer

```bash
sudo rpm -ivh package.rpm           # install, verbose, progress
sudo rpm -Uvh package.rpm           # upgrade (or install if absent)
sudo rpm -e nginx                   # erase
rpm -qa                             # all installed
rpm -qa | grep nginx
rpm -qi nginx                       # info
rpm -ql nginx                       # file list
rpm -qf /etc/nginx/nginx.conf       # which package owns a file
rpm -qc nginx                       # just its config files
rpm -qp --scripts package.rpm       # what scripts it would run - read before trusting
rpm -V nginx                        # VERIFY: which installed files have changed since install
```

`rpm -V` output flags: `5` checksum differs, `S` size, `T` time, `M` mode,
`U`/`G` owner/group, `c` marks a config file. It is the quickest "what did
someone edit" on an RHEL box (Debian: `debsums`).

## The questions you will actually be asked

| Question | Debian | RHEL |
|---|---|---|
| install X | `apt install X` | `dnf install X` |
| remove X and its config | `apt purge X` | `dnf remove X` |
| is X installed, which version | `apt list --installed \| grep X`, `dpkg -l X` | `rpm -q X` |
| which package owns /path | `dpkg -S /path` | `rpm -qf /path` |
| what files did X install | `dpkg -L X` | `rpm -ql X` |
| which package provides command Y | `apt-file search Y` | `dnf provides Y` |
| what changed recently | `/var/log/apt/history.log` | `dnf history` |
| undo the last install | `apt remove` / manual | `dnf history undo` |

## Careful with upgrades

```bash
sudo apt update && sudo apt upgrade      # read the list BEFORE confirming
sudo apt list --upgradable
sudo needrestart                          # which services need restarting after a library upgrade
sudo apt install --only-upgrade nginx     # one package, no others
```

`apt upgrade` never removes packages; `full-upgrade`/`dist-upgrade` may -
on a production box, read what it proposes to remove before typing `y`.

:::exam-tip
Both families may appear; the exam is Ubuntu, so `apt`/`dpkg` are the
likely ones, but know the mapping. "Install package X and make sure it
starts at boot" is two objectives joined: `apt install -y X` then
`systemctl enable --now X`. "Find which package owns /usr/bin/x" is
`dpkg -S`. Always `apt update` before `apt install` in a fresh machine.
:::

## Check yourself

1. What is the difference between `apt remove` and `apt purge`, and
   between `apt upgrade` and `apt full-upgrade`?
2. Which command tells you which package owns `/etc/ssh/sshd_config`, on
   each family?
3. Which RPM command shows which installed files have been modified since
   installation?
