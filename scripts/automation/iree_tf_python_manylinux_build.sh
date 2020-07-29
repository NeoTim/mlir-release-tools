#!/bin/bash
set -e

function die() {
  echo "$@"
  exit 1
}
[ -f "dodo.py" ] || die "Must be run from the repo root"

if [ "$1" != "indocker" ]; then
  set -x
  mkdir -p install
  # Clean up prior?
  # rm -Rf build install .doit.db
  # TODO: Bazel only build reliably on large core systems if running from
  # a ram disk. File an issue with the bazel team.
  dockcross-manylinux2014-bazel-x64 \
    --args "--shm-size=30G --env BAZEL_OUTPUT_BASE=/dev/shm/bazel-out" \
    -- "./$0" indocker
else
  set -x
  export PATH=/opt/python/cp38-cp38/bin:$PATH
  python -m pip install doit
  doit iree_python_deps
  doit iree_tf_default
fi
