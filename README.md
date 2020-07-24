# Build and packaging support for various MLIR projects

This repository contains build infrastructure for assembling and packaging
various MLIR-derived projects that take an out-of-tree dep on LLVM. It is
intended to be used as part of CI and packaging workflows, not necessarily
by developers.

## Quick start

### VM Setup

Clone this repo into the `/base` directory:

```shell
mkdir /base
cd /base
git clone https://github.com/google/mlir-release-tools.git
```

Pre-fetch all deps (can be done periodically to reduce clone times).
```shell
cd /base/mlir-release-tools
./mmr init
./mmr checkout
```

Scripts for setting up a VM are in the scripts/ directory.
