#!/bin/bash
set -e

MRT_SHARED_CACHE_DIR="${MRT_SHARED_CACHE_DIR:-$HOME/.mrtcache}"

function die() {
  echo "$@"
  exit 1
}
[ -f "dodo.py" ] || die "Must be run from the repo root"

function cleanup_outer() {
  set +e
  echo "Pushing to cache..."
  ./scripts/automation/sync_cache.py --push ./cache "$MRT_SHARED_CACHE_DIR"
  echo "Cache push complete"
}

if [ "$1" != "indocker" ]; then
  set -x
  mkdir -p install
  ./scripts/automation/sync_cache.py --pull ./cache "$MRT_SHARED_CACHE_DIR"
  trap cleanup_outer EXIT
  trap cleanup_outer ERR
  dockcross-manylinux2014-x64 "./$0" indocker
else
  set -x
  export PATH=/opt/python/cp38-cp38/bin:$PATH
  export LIT_OPTS="-v"
  # TODO: Bake these into the image.
  python -m pip install doit numpy
  doit npcomp_default
fi
