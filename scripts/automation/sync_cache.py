#!/usr/bin/env python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Synchronizes a cache directory with shared sources.

In general, a top-level cache directory mlir-release-tools/cache is created
and used for all in-build operations, with the expectation that it does not
persist across CI invocations. Scoping in this way (versus having at a random
point on the file-system) also provides some simplicity to container
invocations, since only the mlir-release-tools/ checkout directory needs to
be mounted and accessible.

Typically, cache sensitive pipeline steps will include two calls to this
utility: one at the beginning to populate the local cache and one at the
end to push any changes back upstream as needed.

In the simplest mode, "upstream" is just a dedicated out-of-build directory
on the host which can hold cache artifacts (and is size limited). In the
more complicated scenario, there is also a cloud repo that changes can
be pushed to (and will be fetched from opportunistically as needed, as part
of the build). The latter is not yet implemented.
"""

import argparse
import os
import sys


def create_argument_parser():
  parser = argparse.ArgumentParser(
      prog="sync_cache",
      description=__doc__,
      add_help=True,
      formatter_class=argparse.RawTextHelpFormatter)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--push",
                     dest="mode",
                     action="store_const",
                     const="push",
                     help="Pushes local snapshot to a shared cache")
  group.add_argument(
      "--pull",
      dest="mode",
      action="store_const",
      const="pull",
      help="Pulls changes from a shared cache to a local snapshot")

  parser.add_argument(
      "--size-limit-mb",
      help="Size limit in megabytes of the shared cache (-1 disables pruning)",
      type=int,
      default=20 * 1024)
  parser.add_argument(
      "snapshot_dir",
      help="Snapshot directory that is being pushed from or pulled to",
      type=str)
  parser.add_argument("shared_cache_dir",
                      help="Shared cache directory",
                      type=str)
  return parser


def main(args):
  parser = create_argument_parser().parse_args(args)
  if parser.mode == "push":
    do_push(parser)
  elif parser.mode == "pull":
    do_pull(parser)
  else:
    assert False, "Unreachable"


def do_push(parser):
  shared_cache_dir = parser.shared_cache_dir
  snapshot_dir = parser.snapshot_dir
  if not os.path.exists(snapshot_dir):
    print("Snapshot dir does not exist (not syncing):", snapshot_dir)
  os.makedirs(shared_cache_dir, exist_ok=True)
  with os.scandir(snapshot_dir) as it:
    for entry in it:
      if not entry.is_file():
        continue
      src_file = os.path.join(snapshot_dir, entry.name)
      tgt_file = os.path.join(shared_cache_dir, entry.name)
      if os.path.exists(tgt_file):
        continue
      os.link(src_file, tgt_file)

  # Prune shared cache dir.
  size_limit_mb = parser.size_limit_mb
  if size_limit_mb > 0:
    size_limit_bytes = size_limit_mb * 1024 * 1024
    existing_files = list()
    with os.scandir(shared_cache_dir) as it:
      for entry in it:
        if not entry.is_file():
          continue
        file_path = os.path.join(shared_cache_dir, entry.name)
        stat = entry.stat()
        existing_files.append((file_path, stat.st_mtime_ns, stat.st_size))
    # Sort by mtime
    existing_files.sort(key=lambda t: t[1], reverse=True)
    cum_size = 0
    for file_path, _, size in existing_files:
      cum_size += size
      if cum_size > size_limit_bytes:
        print("Pruning cache file over limit:", file_path)
        os.unlink(file_path)


def do_pull(parser):
  snapshot_dir = parser.snapshot_dir
  shared_cache_dir = parser.shared_cache_dir
  if not os.path.exists(shared_cache_dir):
    print("Shared cache dir does not exist (not syncing):", shared_cache_dir)
  os.makedirs(snapshot_dir, exist_ok=True)
  with os.scandir(shared_cache_dir) as it:
    for entry in it:
      if not entry.is_file():
        continue
      src_file = os.path.join(shared_cache_dir, entry.name)
      tgt_file = os.path.join(snapshot_dir, entry.name)
      if os.path.exists(tgt_file):
        continue
      os.link(src_file, tgt_file)


if __name__ == "__main__":
  main(sys.argv[1:])
