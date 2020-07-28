#!/bin/bash
# For multi-stage pipelines that need to checkout a consistent view of
# the repository, this should be the first step. It will create the following
# files in the root:
#   VERSION_MAP.txt
#
# Arguments should be the unresolved version map to activate by default.
# Example: "iree"
#
# Typically, this will be done with an expression like this, allowing it to
# be overriden by an environment variable (which can be used to a try job or
# other ends).
#   ${VERSION_MAP:-llvm-project iree etc}
set -e

function die() {
  echo "$@"
  exit 1
}
[ -f "dodo.py" ] || die "Must be run from the repo root"

echo "INITIALIZING REPO. VERSION_MAP=$VERSION_MAP"
./mmr init --reference="${MLIR_RELEASE_TOOLS_BASE:-/base/mlir-release-tools}"
./mmr version_map "$@" | tee ./VERSION_MAP.txt
echo "CHECKOUT OUT TREES:"
echo "-------------------"
./mmr status | tee ./VERSION_STATUS.txt
