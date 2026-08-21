## What a certificate is

A **key pair**: a private key you keep, a public key you publish. A
**certificate** is that public key plus an identity (a hostname), signed
by someone a client trusts - a Certificate Authority. TLS uses it to prove
"this server really is example.com" and to negotiate encryption.

```
 private key (server.key)  ──▶  CSR (request: public key + subject)  ──▶  CA signs  ──▶  certificate (server.crt)
        stays on the server                 sent to the CA                             published to clients
```

## Generate a private key

```bash
openssl genrsa -out server.key 2048             # RSA 2048 (3072/4096 for longer life)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out server.key   # the modern form
openssl ecparam -genkey -name prime256v1 -out server-ec.key                     # elliptic curve
chmod 600 server.key                            # ALWAYS - a readable key is a compromised key
openssl rsa -in server.key -noout -text | head  # inspect
openssl rsa -in server.key -pubout -out server.pub   # extract the public key
```

## Create a CSR

```bash
openssl req -new -key server.key -out server.csr
# Country Name (2 letter code) [AU]:UZ
# ...
# Common Name (e.g. server FQDN) []:www.example.com
```

Non-interactive, with the subject on the command line:

```bash
openssl req -new -key server.key -out server.csr \
  -subj "/C=UZ/ST=Tashkent/L=Tashkent/O=Example LLC/OU=IT/CN=www.example.com"
openssl req -in server.csr -noout -text        # verify the subject and key
openssl req -in server.csr -noout -verify      # the signature is self-consistent
```

Modern browsers ignore CN and require **Subject Alternative Names**:

```bash
openssl req -new -key server.key -out server.csr \
  -subj "/CN=www.example.com" \
  -addext "subjectAltName=DNS:www.example.com,DNS:example.com,IP:10.0.0.5"
```

## Self-signed certificates

For internal services and labs - no CA involved, so clients must be told
to trust it explicitly:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key -out server.crt \
  -days 365 -subj "/CN=server.internal" -addext "subjectAltName=DNS:server.internal"
```

`-x509` means "output a certificate, not a request"; `-nodes` means "do not
encrypt the private key" (needed for a service that starts unattended);
`-days` sets the lifetime. One command, key and certificate.

To sign a CSR with your own small CA:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout ca.key -out ca.crt -days 3650 -subj "/CN=My Internal CA"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:www.example.com")
```

## Reading a certificate

```bash
openssl x509 -in server.crt -noout -text                    # everything
openssl x509 -in server.crt -noout -subject -issuer -dates  # the three questions: who, by whom, until when
# subject=CN = www.example.com
# issuer=CN = My Internal CA
# notBefore=Aug 21 10:00:00 2026 GMT
# notAfter=Aug 21 10:00:00 2027 GMT
openssl x509 -in server.crt -noout -ext subjectAltName
openssl x509 -in server.crt -noout -fingerprint -sha256
openssl x509 -in server.crt -noout -checkend 2592000        # will it expire within 30 days? exit 1 = yes
```

**Do the key and certificate match?** Compare the public key hashes - if
these three differ, the service will refuse to start:

```bash
openssl x509 -in server.crt -noout -modulus | openssl sha256
openssl rsa  -in server.key -noout -modulus | openssl sha256
openssl req  -in server.csr -noout -modulus | openssl sha256
```

## Testing a live server

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null
openssl s_client -connect example.com:443 -showcerts </dev/null | openssl x509 -noout -dates
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -subject -issuer -dates
curl -vI https://example.com                    # curl reports the certificate chain and any error
```

## Formats and conversion

| Format | Extension | What |
|---|---|---|
| PEM | `.pem` `.crt` `.key` `.csr` | base64 text between `-----BEGIN ...-----` lines - the Linux default |
| DER | `.der` `.cer` | binary |
| PKCS#12 | `.p12` `.pfx` | key + certificate + chain in one password-protected file (Windows, Java) |

```bash
openssl x509 -in cert.der -inform DER -out cert.pem -outform PEM
openssl pkcs12 -export -out bundle.p12 -inkey server.key -in server.crt -certfile ca.crt
openssl pkcs12 -in bundle.p12 -nodes -out all.pem
```

## Where they live, and trusting a CA

```bash
/etc/ssl/certs/      /etc/ssl/private/          # Debian/Ubuntu
/etc/pki/tls/certs/  /etc/pki/tls/private/      # RHEL family

sudo cp my-ca.crt /usr/local/share/ca-certificates/my-ca.crt && sudo update-ca-certificates   # Debian
sudo cp my-ca.crt /etc/pki/ca-trust/source/anchors/ && sudo update-ca-trust                    # RHEL
```

:::warning
Private keys are `chmod 600`, owned by root or the service user, and never
leave the host. A key committed to Git or copied over a chat is
compromised: revoke and reissue. `-nodes` (no passphrase) is normal for
servers, which is exactly why the file permissions carry the whole
burden.
:::

:::exam-tip
The likely tasks: generate a key and a CSR with a given subject
(`openssl genrsa` + `openssl req -new -subj`), create a self-signed
certificate valid for N days (`openssl req -x509 -days N -nodes`), and
read a certificate's subject/issuer/expiry (`openssl x509 -noout -subject
-issuer -dates`). Memorise those three command shapes; `man openssl-req`
and `man openssl-x509` fill in the rest.
:::

## Check yourself

1. What three things does a CSR contain, and what does the CA add?
2. How do you check that a private key and a certificate belong together?
3. Which command shows a certificate's expiry date, and which tests a
   live server's certificate?
