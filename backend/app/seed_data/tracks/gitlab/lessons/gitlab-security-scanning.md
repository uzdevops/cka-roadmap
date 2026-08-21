## Scanners you include, not write

GitLab ships security scanners as templates (and, newer, as components).
Adding one is one `include:` line; the scanner job produces a report
artifact that GitLab renders in the MR and on the project's security
pages.

```yaml
include:
  - template: Jobs/SAST.gitlab-ci.yml                 # static analysis of source
  - template: Jobs/Secret-Detection.gitlab-ci.yml     # leaked tokens/keys in the history
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml  # known CVEs in package-lock.json
  - template: Jobs/Container-Scanning.gitlab-ci.yml   # CVEs in the built image

container_scanning:
  variables:
    CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"   # scan what you just pushed
  needs: [publish-image]
```

Every template creates jobs in the `test` stage (add it if you renamed
your stages) with `rules:` that run them on branches and MRs. They are
`allow_failure: true` by default - **they report, they do not block** -
which is the right first week; blocking comes with policies.

| Scanner | Looks at | Typical finding |
|---|---|---|
| SAST | your source (language-detected) | SQL built from strings, `eval`, weak crypto |
| Secret Detection | the diff / history | an AWS key committed "just for testing" |
| Dependency Scanning | lock files | `lodash < 4.17.21` prototype pollution |
| Container Scanning | the image's OS packages and libraries | `openssl` CVE in the base layer |
| DAST | a running URL | reflected XSS, missing headers (needs an environment) |

## What you see

- MR widget: **Security scanning** - new vulnerabilities introduced by the
  MR, with severity and a link to the line / package / layer.
- *Secure → Vulnerability report*: everything known about the default
  branch, triageable (confirm, dismiss with reason, create issue).
- The `gl-*-report.json` artifacts, downloadable for audit.

## Turning reports into gates

Three escalating options:

1. **Merge request approval policy** (*Secure → Policies*): "any new
   critical vulnerability requires approval from @security". The MR is not
   blocked, but it cannot merge without that person.
2. **Scan execution policy**: force these scanners to run in every project
   in the group, whatever their YAML says - the scanners cannot be removed
   by editing a file.
3. **Fail the job** yourself for a hard line:

```yaml
container_scanning:
  allow_failure: false
  variables:
    CS_SEVERITY_THRESHOLD: CRITICAL     # fail on critical findings
```

Start with 1 and 2. A pipeline that fails on every medium CVE in a base
image is a pipeline people disable.

## Secrets that are already out

Secret Detection finding a key means the key is **compromised**: rotate it
first, then rewrite history if you must. Pre-push hooks (`gitleaks`) in
developers' repos stop the commit before it exists; the pipeline scanner
is the net under the net.

## Self-check

- What does a scanner template add to a pipeline, and what is its default
  effect on the merge?
- Which mechanism guarantees a scanner runs even if someone deletes the
  include line?
- A secret is detected in an MR. What is the first action?
