#!/bin/bash
# Asks the remote whether main has moved, and hands over to cka-deploy if it
# has. Runs every five minutes from cka-check.timer.
#
# Deliberately does nothing but compare and trigger: fetch is cheap and safe to
# repeat, while anything that mutates the working tree belongs in the deploy
# unit where a failure is recorded against the thing that actually failed.
set -euo pipefail

REPO="${CKA_REPO:-/opt/projects/cka-roadmap}"

cd "$REPO"

git fetch --quiet origin

local_rev=$(git rev-parse HEAD)
remote_rev=$(git rev-parse '@{u}')

if [ "$local_rev" = "$remote_rev" ]; then
    echo "up to date at ${local_rev:0:8}"
    exit 0
fi

echo "new commits upstream: ${local_rev:0:8} -> ${remote_rev:0:8}"
git --no-pager log --oneline "${local_rev}..${remote_rev}" | head -10

# --no-block so a build that outlasts the five-minute interval does not hold
# this unit open. Re-triggering an already-running deploy is a no-op.
systemctl start --no-block cka-deploy.service
echo "triggered cka-deploy.service"
