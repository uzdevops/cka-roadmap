## One identity across many hosts

Local accounts do not scale: fifty servers means fifty copies of every
user, fifty password changes, fifty places to forget to remove someone.
A **directory** (LDAP, or Active Directory, which speaks LDAP) holds users
and groups centrally; each host asks the directory instead of reading
`/etc/passwd`.

```
 login → PAM (authentication) ─┐
                               ├→ SSSD ──cache──▶ LDAP / AD server
 id, ls -l → NSS (identity) ───┘
```

Two subsystems, one daemon:

- **NSS** (Name Service Switch) answers "who is uid 1234, what groups does
  alice have" - configured in `/etc/nsswitch.conf`.
- **PAM** answers "is this password correct, may this user log in" -
  configured in `/etc/pam.d/*`.
- **SSSD** implements both against the directory, and **caches** the
  answers so logins still work when the network does not.

## Installing

```bash
sudo apt install sssd sssd-tools libnss-sss libpam-sss ldap-utils oddjob-mkhomedir
sudo dnf install sssd sssd-ldap oddjob-mkhomedir openldap-clients
```

## Configuring SSSD

```bash
sudo vi /etc/sssd/sssd.conf
```

```ini
[sssd]
services = nss, pam
domains = example.com

[domain/example.com]
id_provider = ldap
auth_provider = ldap
ldap_uri = ldaps://ldap.example.com:636
ldap_search_base = dc=example,dc=com
ldap_default_bind_dn = cn=sssd,ou=services,dc=example,dc=com
ldap_default_authtok = <bind password>
ldap_tls_reqcert = demand
ldap_tls_cacert = /etc/ssl/certs/company-ca.crt
cache_credentials = true
enumerate = false
override_homedir = /home/%u
default_shell = /bin/bash
ldap_id_use_start_tls = false
access_provider = simple
simple_allow_groups = linux-admins, developers
```

```bash
sudo chmod 600 /etc/sssd/sssd.conf         # SSSD REFUSES to start otherwise - it holds a bind password
sudo chown root:root /etc/sssd/sssd.conf
sudo systemctl enable --now sssd
sudo systemctl status sssd
```

`cache_credentials = true` is what lets a laptop log in offline;
`access_provider = simple` with `simple_allow_groups` is the simplest way
to say "only these directory groups may log in to this host".

## Wiring NSS and PAM

```bash
sudo pam-auth-update                       # Debian: tick "SSS authentication" and "create home directory"
sudo authselect select sssd with-mkhomedir --force     # RHEL family
grep -E "^(passwd|group|shadow)" /etc/nsswitch.conf
# passwd:  files sss
# group:   files sss
# shadow:  files sss
```

`files sss` means "look in `/etc/passwd` first, then ask SSSD" - local
accounts keep working and win on conflicts.

Home directories for directory users do not exist until someone logs in;
`pam_mkhomedir` (via `oddjob-mkhomedir` or `pam-auth-update`) creates them
from `/etc/skel` at first login.

```
# /etc/pam.d/common-session
session optional pam_mkhomedir.so skel=/etc/skel umask=0077
```

## Verifying

```bash
getent passwd alice                # resolves through NSS: if this works, identity is fine
getent group developers
id alice
su - alice                         # tests PAM: if getent works and this fails, it is authentication
sudo sssctl domain-status example.com
sudo sssctl user-checks alice -a auth
ldapsearch -x -H ldaps://ldap.example.com -b "dc=example,dc=com" "(uid=alice)"     # ask the server directly
sudo systemctl restart sssd
sudo rm -rf /var/lib/sss/db/* && sudo systemctl restart sssd    # clear the cache when data looks stale
sudo journalctl -u sssd -f
```

The diagnosis order is always the same: `getent passwd` (NSS) → `su -`
(PAM) → `ldapsearch` (the server and the bind credentials) → SSSD logs.

## Joining Active Directory

```bash
sudo apt install realmd sssd adcli krb5-user samba-common-bin
realm discover example.com
sudo realm join --user=Administrator example.com
realm list
sudo realm permit --groups 'EXAMPLE\linux-admins'
id 'EXAMPLE\alice'; id alice@example.com
sudo realm leave example.com
```

`realm join` writes the SSSD and Kerberos configuration for you - the
usual path for AD, where hand-writing `sssd.conf` is unnecessary.

## Common failures

| Symptom | Cause |
|---|---|
| `getent passwd alice` empty | NSS not pointed at `sss`, SSSD down, wrong `search_base` |
| identity works, login fails | PAM not configured (`pam-auth-update`/`authselect`), or `access_provider` rules |
| `Could not start TLS ... peer certificate` | the CA is not in `ldap_tls_cacert`, or the hostname does not match |
| SSSD refuses to start | `sssd.conf` not mode 0600, or a syntax error - `journalctl -u sssd` |
| no home directory at login | `pam_mkhomedir` not enabled |
| works, then stops after a password change | stale cache - restart SSSD or clear `/var/lib/sss/db` |
| sudo does not apply to directory users | add `sudoers: files sss` to nsswitch, or a local `/etc/sudoers.d` rule for the group |

:::warning
`ldap_default_authtok` is a password in a config file - hence mode 0600 and
a service account with **read-only** rights over the minimum subtree.
Never point production at `ldap://` without TLS: bind passwords and user
data cross the network in clear. `ldap_tls_reqcert = never` disables the
one check that makes LDAPS meaningful.
:::

:::exam-tip
A full LDAP setup is a long task, so an exam version is usually narrower:
install the packages, write the given `sssd.conf`, set its permissions to
0600, enable the service, enable home-directory creation, and prove it with
`getent passwd <directory-user>` and `id`. The permissions on
`/etc/sssd/sssd.conf` and the `files sss` line in nsswitch are the two
details people forget.
:::

## Check yourself

1. What do NSS and PAM each answer, and which file configures each?
2. Which command proves identity resolution works, and which proves
   authentication works?
3. Why must `/etc/sssd/sssd.conf` be mode 0600, and what happens if it is
   not?
