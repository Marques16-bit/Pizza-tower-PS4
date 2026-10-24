#!/usr/bin/env bash
# Baixa o Butterscotch na versão fixada em project.env para vendor/butterscotch.
set -euo pipefail
cd "$(dirname "$0")/.."
source project.env
mkdir -p vendor
if [ ! -d vendor/butterscotch/.git ]; then
  git clone --branch "$BUTTERSCOTCH_BRANCH" "$BUTTERSCOTCH_REPO" vendor/butterscotch
fi
git -C vendor/butterscotch checkout "$BUTTERSCOTCH_REF"
git -C vendor/butterscotch submodule update --init --recursive || true
