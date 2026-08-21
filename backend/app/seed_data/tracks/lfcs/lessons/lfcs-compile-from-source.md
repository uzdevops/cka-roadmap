## When packages are not enough

Sometimes there is no package: a version newer than the repository has, a
build with an option the packager disabled, or software that only ships
source. The classic sequence is three commands - and a fourth,
`checkinstall` or a package, if you want it removable.

```bash
./configure && make && sudo make install
```

## Build dependencies first

```bash
sudo apt install build-essential          # gcc, g++, make, libc-dev  (Debian/Ubuntu)
sudo dnf groupinstall "Development Tools" # (RHEL family)
sudo apt install pkg-config autoconf automake libtool cmake
sudo apt build-dep nginx                  # the exact build deps of a packaged program (needs deb-src lines)
```

Each `configure` failure names a missing library: `libssl-dev`,
`zlib1g-dev`, `libpcre3-dev` - the `-dev`/`-devel` packages carry the
headers a compiler needs, which the runtime package does not.

## The full walk

```bash
cd /usr/local/src
sudo wget https://nginx.org/download/nginx-1.26.1.tar.gz
sudo wget https://nginx.org/download/nginx-1.26.1.tar.gz.asc     # signature, if published
tar -xzf nginx-1.26.1.tar.gz
cd nginx-1.26.1
ls                       # README, INSTALL, configure, Makefile.in, src/
less INSTALL             # READ THIS - it lists options and prerequisites
```

```bash
./configure --help | less
./configure --prefix=/usr/local/nginx --with-http_ssl_module
# checking for OS ... Linux
# checking for C compiler ... found
# ./configure: error: the HTTP rewrite module requires the PCRE library.   ← install libpcre3-dev, rerun
make -j"$(nproc)"        # compile, using every CPU
make test                # or `make check`, if the project has tests
sudo make install
```

| Step | Does |
|---|---|
| `./configure` | checks your system for compilers and libraries, reads your `--options`, writes the `Makefile` |
| `make` | compiles - no root needed, and nothing has touched the system yet |
| `sudo make install` | copies binaries, libraries, man pages and configs into `--prefix` |
| `sudo make uninstall` | removes them **if** the project implements it - many do not |

`--prefix=/usr/local` is the default and the right place: `/usr/local/bin`,
`/usr/local/lib`, `/usr/local/etc`. Never install into `/usr/bin` - that
belongs to the package manager, and a future package update will collide.

Some projects use CMake or Meson instead:

```bash
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr/local && cmake --build build -j"$(nproc)" && sudo cmake --install build
meson setup build --prefix=/usr/local && ninja -C build && sudo ninja -C build install
```

## After installing

```bash
which nginx; nginx -V                     # -V shows the configure options it was built with
echo /usr/local/lib | sudo tee /etc/ld.so.conf.d/local.conf && sudo ldconfig    # if libraries went there
export PATH=/usr/local/nginx/sbin:$PATH   # add to /etc/profile.d/ to make it permanent
```

Then make it a service (the systemd lesson) - source installs bring no
unit file, no logrotate config and no user account; those are yours to
write.

## The maintenance problem

A source install is invisible to `apt`/`dnf`: no security updates, no
dependency tracking, no clean removal. Two ways to keep it manageable:

```bash
sudo apt install checkinstall
sudo checkinstall            # runs make install AND builds a .deb, so dpkg -r removes it later
```

or install each version under its own prefix and switch with a symlink:

```
/opt/nginx-1.26.1/  /opt/nginx-1.27.0/   and   /opt/nginx -> nginx-1.27.0
```

Rolling back is then one `ln -sfn`.

:::warning
Prefer a package. A compiled `openssl` or `nginx` will not get the next
security update unless **you** rebuild it, and "we compiled it in 2023" is
how old vulnerabilities survive. Compile when there is a concrete reason,
record the reason and the build command, and put a reminder in place to
watch upstream releases.
:::

:::exam-tip
A compile task on the exam is small and self-contained: a tarball is on
disk, extract it, `./configure --prefix=...`, `make`, `make install`,
verify the binary runs. Read `INSTALL`/`README` first, install
`build-essential` if `configure` cannot find a compiler, and remember that
only the last step needs root.
:::

## Check yourself

1. What does each of `./configure`, `make` and `make install` do, and
   which needs root?
2. Why `--prefix=/usr/local` and not `/usr`?
3. What are the two drawbacks of a source install compared with a package,
   and how does `checkinstall` help?
