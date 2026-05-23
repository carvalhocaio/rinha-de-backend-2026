#!/usr/bin/env bash
set -euo pipefail

# $1=participant $2=repo-url $3=submission-id $4=commit $5=issue-number
#
# exemplo:
#   ./post-run.sh zanfranceschi https://github.com/zanfranceschi/repo clojure abc1234 99

PARTICIPANT="${1:?participant obrigatório}"
REPO_URL="${2:?repo-url obrigatório}"
SUBMISSION_ID="${3:?submission-id obrigatório}"
COMMIT="${4:?commit obrigatório}"
ISSUE="${5:-}"

