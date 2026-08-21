## Booking

- Buy the exam at training.linuxfoundation.org (the CKA is a Linux
  Foundation / CNCF exam, delivered by PSI). The purchase includes **one
  free retake** and, at the time of writing, two sessions of the
  killer.sh simulator - use them after mock 3, not before.
- The voucher is valid for a year; the **exam date** is booked separately
  in the portal, any day, most hours. Book for a time of day you are
  sharp, two to three weeks out, so the date is real.
- Read the **Candidate Handbook** and the **Important Instructions** page
  the week before. Rules change (allowed domains, ID requirements, room
  rules); this lesson is not a substitute.

## The day before

- Run the PSI **system check** on the machine and network you will use:
  browser, webcam, microphone, screen sharing. One external monitor or the
  laptop screen - not both.
- Government **ID** with a name matching the booking exactly.
- A **clean desk** in a quiet room: no paper, no second device, no notes on
  the wall, nothing on the desk but the machine. The proctor will ask you
  to pan the camera around the room and under the desk.
- Water in a clear container if you want it.
- The drills once; the imperative table once; then stop. Sleep.

## The day

- Check in **30 minutes early**; the ID and room check takes time.
- The exam runs in PSI's secure browser in a **remote desktop** (XFCE):
  a terminal and a Firefox that is restricted to the allowed docs sites.
  Your own browser and bookmarks are not there. Copy-paste works inside the
  remote desktop; `Ctrl+Shift+C/V` in the terminal.
- Minute zero, before task 1: `alias k`, `$do`, vim settings, one `k get
  nodes` to see the terminal works.
- Every task: **read twice**, `kubectl config use-context` as given, do,
  **verify**, `exit` any ssh, next. Use the built-in notepad for skipped
  tasks.
- The hard question: 5 minutes, then skip and return. Partial credit exists;
  an unattempted easy task is worth more than a stuck hard one.
- Results arrive by email within 24 hours (often much sooner). Pass is
  **66%**.

## If it does not go well

One free retake - book it for two to three weeks later, not the next day.
The score report lists domains; the weak-domain lesson applies directly.
Most second attempts pass, and the first attempt is the best mock exam you
will ever take.

## After the CKA

The certificate is valid for **two years**. What it is worth beyond the
PDF: you can now run a cluster, and you know which questions to ask about
one you did not build. Where next depends on what you do all day:

| Direction | Next certification | On this platform |
|---|---|---|
| you write and ship applications on Kubernetes | **CKAD** - Pods, configs, probes, Jobs, Helm, Services, NetworkPolicies, from the developer's seat; 2 hours, overlaps heavily with weeks 3-8 | CKAD track |
| you secure clusters | **CKS** - requires a current CKA; cluster hardening, supply chain, runtime security, admission controllers; the hardest of the three | CKS track |
| you run the Linux underneath | **LFCS** - storage, networking, users, services, shell scripting on Linux; the half of "node troubleshooting" this track only touched | LFCS track |
| you run many clusters in production | no exam for this - GitOps (Argo CD, Flux), observability (Prometheus, Loki), multi-cluster, cost; the DevOps track's later modules | DevOps platform |

And the habits that carry over regardless: read the Events first, change
one thing, verify, and never write YAML from a blank file.

:::tip
Schedule the next thing before the glow fades. A CKAD or CKS voucher bought
the week you pass the CKA is the cheapest way to make sure the twenty
weeks of habit do not evaporate.
:::

## Check yourself

1. What three things must be true of your room and desk before the
   proctor lets you start?
2. Where do you look up documentation during the exam, and why do your
   own bookmarks not help?
3. Which certification would you take next, and why?
