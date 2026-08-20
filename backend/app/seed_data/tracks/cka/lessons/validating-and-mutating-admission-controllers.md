## Admission you write yourself

The built-in plugins cover common policy. For anything else - "every Pod in
this namespace must carry a `team` label", "inject our logging sidecar into
everything", "refuse images from registries we do not trust" - the API server
can call **your** HTTP service and let it decide. Two built-in plugins do the
calling:

- **MutatingAdmissionWebhook** - your service may return a JSON patch that is
  applied to the object.
- **ValidatingAdmissionWebhook** - your service returns allowed or denied,
  with a message.

Mutating webhooks run first (so validating ones see the final object), then
schema validation, then validating webhooks. Several mutating webhooks run
in sequence; validating webhooks run in parallel, and any one of them can
refuse.

```
object ─▶ [mutating webhook A] ─▶ [mutating webhook B] ─▶ validate schema ─▶ [validating webhooks...] ─▶ etcd
```

## The three parts

1. **A webhook server** - any HTTPS service that accepts an
   `AdmissionReview` request and answers with an `AdmissionReview` response.
   Usually runs in the cluster as a Deployment plus Service; must serve TLS
   with a certificate the API server trusts.
2. **A configuration object** that tells the API server when to call it and
   where:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy.example.com
webhooks:
  - name: pod-policy.example.com
    clientConfig:
      service:
        namespace: webhook-demo
        name: webhook-server
        path: /validate
      caBundle: <base64 CA that signed the server cert>
    rules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["pods"]
    admissionReviewVersions: ["v1"]
    sideEffects: None
    failurePolicy: Fail              # or Ignore
    timeoutSeconds: 5
    namespaceSelector: {}            # optionally limit to some namespaces
```

   `MutatingWebhookConfiguration` has the same shape.

3. **The response** your server sends:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "<same uid as the request>",
    "allowed": false,
    "status": {"message": "pods must set runAsNonRoot"}
  }
}
```

   A mutating response adds `"patchType": "JSONPatch"` and a base64-encoded
   JSON patch in `"patch"`.

## failurePolicy is the dangerous field

`Fail` (the default) means: if the webhook is unreachable, times out or
returns garbage, the request is **refused**. That is correct for security
policy and catastrophic when the webhook's own Pods cannot start because the
webhook refuses them. `Ignore` means: if it cannot be reached, let the request
through.

:::warning
A cluster where "nothing can be created any more" and every error mentions
`failed calling webhook` has a webhook whose service is down with
`failurePolicy: Fail`. The recovery is to delete or edit the
`*WebhookConfiguration` object - that is not a webhooked resource, so it still
works - fix the service, and re-create the configuration.
:::

```bash
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations
kubectl describe validatingwebhookconfiguration pod-policy.example.com
kubectl delete validatingwebhookconfiguration pod-policy.example.com   # the emergency exit
```

## Seeing one work

```bash
kubectl run demo --image=nginx
# Error from server: admission webhook "pod-policy.example.com" denied the request: pods must set runAsNonRoot

# with a mutating webhook that injects a securityContext instead:
kubectl run demo --image=nginx
kubectl get pod demo -o jsonpath='{.spec.securityContext}'
# {"runAsNonRoot":true,"runAsUser":1234}   <- you never wrote this
```

:::exam-tip
The exam will not ask you to write a webhook server. It can ask you to
**register** one from supplied manifests (Deployment, Service, the
configuration object with a caBundle), to explain why a request was rejected,
or to diagnose "failed calling webhook". Know the three parts and the
`failurePolicy` trap and you have it.
:::

## The built-in alternative: ValidatingAdmissionPolicy

Since Kubernetes 1.30 you can write simple validation **without a server**,
as CEL expressions in a `ValidatingAdmissionPolicy` object:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-team-label
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "has(object.metadata.labels) && 'team' in object.metadata.labels"
      message: "every Deployment needs a team label"
```

plus a `ValidatingAdmissionPolicyBinding` to switch it on. No TLS, no Pods,
no failurePolicy problem - for simple rules it is the better tool.

## Check yourself

1. In what order do mutating webhooks, schema validation and validating
   webhooks run, and why that order?
2. Nothing can be created in the cluster and every error says `failed calling
   webhook`. What happened, and what is the recovery?
3. What does the API server need in `clientConfig` to trust your webhook
   server, and what happens if it is wrong?
