#!/bin/bash
# Create scripts for dockcross images we care about.
# Run with sudo.
DOCKCROSS_IMAGES="manylinux2014-x64"

for img in $DOCKCROSS_IMAGES; do
  echo "### Setting up dockcross image $img ###"
  docker run --rm dockcross/$img > /usr/local/bin/dockcross-$img
  chmod a+x /usr/local/bin/dockcross-$img
done
