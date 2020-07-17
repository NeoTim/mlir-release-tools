# Build and packaging support for various MLIR projects

This repository contains build infrastructure for assembling and packaging
various MLIR-derived projects that take an out-of-tree dep on LLVM. It is
intended to be used as part of CI and packaging workflows, not necessarily
by developers.

## Quick start

### Install dependencies

```shell
# Or get it some other way.
python3 -m pip install doit
```

```shell
TODO: Fetch the 'mmr' package once open-sourced.
```

### Checkout

```shell
mkdir new_repo
cd new_repo
mmr init
mmr checkout https://github.com/google/mlir-release-tools
cd mlir-release-tools
```

### Sync to a revision cone (if not building at head)

```shell
# Syncs the source-graph to the revisions from IREE
cd external/iree
mmr focus
cd ../..
```

### Build

```shell
doit llvm
doit iree_default
doit npcomp
```

Artifacts will be created under the `install/` directory by default.s
