## Where packages come from

A repository is a server holding packages plus a signed index. Your
machine has a list of them; `apt update` / `dnf makecache` downloads the
indexes; installs come from whichever repository offers the best version.

## Debian/Ubuntu: sources.list

```bash
cat /etc/apt/sources.list
ls /etc/apt/sources.list.d/
```

```
deb http://archive.ubuntu.com/ubuntu noble main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu noble-security main restricted
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe
# deb-src ...   ← source packages, for compiling
```

`deb` type, URL, **suite** (`noble`, `noble-updates`, `noble-backports`),
then **components**: `main` (supported free), `restricted` (drivers),
`universe` (community), `multiverse` (non-free).

The modern deb822 form, one file per repository:

```
# /etc/apt/sources.list.d/docker.sources
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
```

## Adding a third-party repository, correctly

Repositories are trusted by GPG key. The old `apt-key add` is deprecated
(it trusted a key for *every* repo); the current way puts the key in
`/etc/apt/keyrings` and references it from the source:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc > /dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
apt-cache policy docker-ce         # which repo the candidate version comes from
```

Simpler helpers:

```bash
sudo add-apt-repository universe                 # enable a component
sudo add-apt-repository ppa:user/ppa-name        # an Ubuntu PPA (adds source + key)
sudo add-apt-repository --remove ppa:user/ppa-name
sudo apt update
```

## Pinning and priorities (Debian)

```bash
apt-cache policy nginx
# Installed: 1.24.0-1
# Candidate: 1.26.0-1
#   500 https://nginx.org/packages/ubuntu noble/nginx amd64 Packages
#   500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages
```

```
# /etc/apt/preferences.d/nginx
Package: nginx
Pin: origin nginx.org
Pin-Priority: 900
```

Higher priority wins. Use it when two repositories offer the same package
and you want a specific origin; `apt-mark hold` is the blunter tool for
"never upgrade this".

## RHEL family: .repo files

```bash
ls /etc/yum.repos.d/
cat /etc/yum.repos.d/docker-ce.repo
```

```ini
[docker-ce-stable]
name=Docker CE Stable - $basearch
baseurl=https://download.docker.com/linux/centos/$releasever/$basearch/stable
enabled=1
gpgcheck=1
gpgkey=https://download.docker.com/linux/centos/gpg
```

```bash
dnf repolist                                  # enabled repositories
dnf repolist --all                            # including disabled
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf config-manager --set-enabled crb
sudo dnf config-manager --set-disabled docker-ce-test
sudo rpm --import https://download.docker.com/linux/centos/gpg
sudo dnf install epel-release
sudo dnf clean all && sudo dnf makecache
sudo dnf --disablerepo=* --enablerepo=base install x       # for one command only
```

## Verifying and troubleshooting

```bash
apt-key list                       # deprecated but still shows legacy keys
ls /etc/apt/trusted.gpg.d/ /etc/apt/keyrings/
sudo apt update 2>&1 | grep -i "NO_PUBKEY\|not signed\|Failed"
```

| Message | Cause | Fix |
|---|---|---|
| `NO_PUBKEY 1234ABCD` | the repository's key is not installed | fetch the key into `/etc/apt/keyrings` and reference it with `signed-by` |
| `Repository ... is not signed` | no key or wrong key path | same |
| `404 Not Found` on `apt update` | wrong suite/codename, or the repo dropped your release | fix the codename in the source file |
| `Unable to locate package X` | the component or repo providing it is not enabled | `add-apt-repository universe`, then `apt update` |
| `Conflicting values set for option Signed-By` | the same repo listed twice with different keys | remove the duplicate `.list`/`.sources` file |
| dnf: `GPG check FAILED` | key missing or package tampered | import the correct key; never `gpgcheck=0` to "fix" it |

Local repositories, for air-gapped machines:

```bash
sudo apt install dpkg-dev && dpkg-scanpackages . | gzip > Packages.gz     # a directory as a repo
echo "deb [trusted=yes] file:/srv/repo ./" | sudo tee /etc/apt/sources.list.d/local.list
sudo dnf install createrepo_c && createrepo_c /srv/repo                    # RPM side
```

:::warning
`gpgcheck=0`, `[trusted=yes]` and `--allow-unauthenticated` all mean "run
whatever this server sends me as root". They exist for local mirrors you
built. Never use them to silence a key error from the internet - fix the
key.
:::

:::exam-tip
Likely task: "add repository R with key K and install package P from it".
The sequence is key → source file → `apt update` → `apt install`, then
`apt-cache policy P` to prove it came from R. Know where the files live
(`/etc/apt/sources.list.d/`, `/etc/yum.repos.d/`) and that nothing takes
effect until the index is refreshed.
:::

## Check yourself

1. What are the four parts of a `deb` line in sources.list?
2. Why is `apt-key add` deprecated, and what replaces it?
3. `apt update` reports `NO_PUBKEY`. What is missing and what must not be
   your fix?
