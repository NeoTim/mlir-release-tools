#!/bin/bash
# Create scripts for dockcross images we care about.
# Run with sudo.
DOCKCROSS_IMAGES="dockcross/manylinux2014-x64 gcr.io/iree-oss/manylinux2014-bazel-x64"
BIN_DIR="${1:-/usr/local/bin}"
for url in $DOCKCROSS_IMAGES; do
  echo "### Setting up dockcross image $url ###"
  img="$(basename $url)"
  docker run --rm $url > $BIN_DIR/dockcross-$img
  chmod a+x $BIN_DIR/dockcross-$img
done
