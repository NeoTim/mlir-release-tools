#!/bin/bash
# Checks out and sets versions for a step.
# Typically a pipeline will start by running pipeline_init_version_map.sh
# to resolve concrete revisions for all subsequent steps. Then this script
# will read the version map from VERSION_MAP.txt and checkout/set it.
set -e

function die() {
  echo "$@"
  exit 1
}
[ -f "dodo.py" ] || die "Must be run from the repo root"

# Find existing version map.
VERSION_MAP=""
if [ -f "VERSION_MAP.txt" ]; then
  VERSION_MAP="$(cat VERSION_MAP.txt)"
fi
echo "INITIALIZING REPO. VERSION_MAP=$VERSION_MAP"
./mmr init --reference="${MLIR_RELEASE_TOOLS_BASE:-/base/mlir-release-tools}"
echo "CHECKING OUT:"
echo "-------------"
./mmr checkout
echo "SETTING VERSION MAP:"
echo "--------------------"
./mmr version_map --set --no-fetch $VERSION_MAP
echo "CHECKOUT OUT TREES:"
echo "-------------------"
./mmr status | tee ./VERSION_STATUS.txt
