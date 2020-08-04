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

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import traceback

import builder

CACHE_DIR_ENV_VAR = "MRT_CACHE_DIR"


def get_cache_root():
  env_value = os.environ.get(CACHE_DIR_ENV_VAR)
  if env_value:
    return Path(env_value)
  else:
    return builder.TOP_DIR.joinpath("cache").resolve()


def read_git_state(src_dir):
  """Generates git state suitable for hashing as a version spec."""

  def run(*args):
    return subprocess.check_output(args, cwd=str(src_dir)).decode("UTF-8")

  state = "\n".join([
      run("git", "rev-parse", "HEAD"),
      run("git", "submodule", "status"),
      run("git", "diff"),
  ])
  module_deps_path = Path(src_dir).joinpath("module_deps.json")
  if module_deps_path.exists():
    state += "\n"
    state += module_deps_path.read_text(encoding="UTF-8")
  return state


class InstallCache:
  """Task generator for caching installation artifacts.

  This is typically used to generate cache tasks which delegate to a local
  build/install task as needed.
  """

  def __init__(self, *, identifier: str, cache_key: str, install_task: str,
               version_data_lambda):
    self.identifier = identifier
    self.cache_key = cache_key
    self.install_task = install_task
    self.version_data_lambda = version_data_lambda
    self._version_hash = None

  @property
  def version_hash(self):
    if self._version_hash is None:
      hash_data = ":".join(
          [self.identifier, self.cache_key,
           self.version_data_lambda()]).encode("UTF-8")
      self._version_hash = hashlib.sha224(hash_data).hexdigest()
    return self._version_hash

  @property
  def install_dir(self):
    """The installation directory that is cached."""
    return builder.get_install_root().joinpath(self.identifier)

  @property
  def marker_file(self):
    """A marker file indicating successful install."""
    install_dir = self.install_dir
    return install_dir.parent.joinpath(".installed_" + install_dir.name)

  @property
  def cache_archive_file(self):
    """The installation cache archive file."""
    return get_cache_root().joinpath("{}_{}.tar".format(self.cache_key,
                                                        self.version_hash))

  def install_is_ok(self):
    if not self.marker_file.exists() or not self.install_dir.exists():
      return False

    # Verify that the marker has the correct version hash.
    marker_version_hash = self.marker_file.read_text(encoding="UTF-8")
    if marker_version_hash != self.version_hash:
      print("Installation version hash mismatch. Discarding.")
      self.marker_file.unlink()
      if self.cache_archive_file.exists():
        self.cache_archive_file.unlink()
      return False
    return True

  def touch_marker_file(self):
    self.marker_file.write_text(self.version_hash, encoding="UTF-8")

  def create_cache_archive_file(self):
    # Create the tarfile.
    archive_path = self.cache_archive_file
    archive_tmp_path = archive_path.parent.joinpath("." + archive_path.name +
                                                    ".tmp")
    install_dir = self.install_dir

    if archive_path.exists():
      return
    if archive_tmp_path.exists():
      archive_tmp_path.unlink()

    print("Creating archive cache file:", archive_path)
    os.makedirs(archive_tmp_path.parent, exist_ok=True)
    subprocess.check_call(
        ["tar", "cf", str(archive_tmp_path), install_dir.name],
        cwd=str(install_dir.parent))
    # Atomic rename into place.
    archive_tmp_path.rename(archive_path)

  def expand_cache_archive_file(self):
    archive_path = self.cache_archive_file
    if not archive_path.exists(): return
    install_dir = self.install_dir
    os.makedirs(install_dir.parent, exist_ok=True)
    print("Extracting cache archive file:", archive_path)
    try:
      subprocess.check_call(
          ["tar", "xf", str(archive_path), install_dir.name],
          cwd=str(install_dir.parent))
    except:
      if install_dir.exists():
        shutil.rmtree(install_dir)
      raise
    else:
      self.touch_marker_file()

  def store_install_to_cache(self):
    self.create_cache_archive_file()
    # TODO: Publish to shared cache.

  def fetch_install_from_cache(self):
    # TODO: Fetch from shared cache.
    self.expand_cache_archive_file()

  def yield_tasks(self, *, taskname=None, basename=None):
    """Yields all tasks to cache and locally build as necessary."""

    def subtask(suffix, qualified=False):
      subtask_name = basename + ":" + suffix if basename is not None else suffix
      if qualified and taskname is not None:
        return taskname + ":" + subtask_name
      else:
        return subtask_name

    def fetch_cache():
      # Skip if ok.
      if self.install_is_ok():
        print("Not fetching/building {}: Already exists".format(
            self.identifier))
        return

      # Try to fetch.
      print("Fetching {} from cache".format(self.identifier))
      try:
        self.fetch_install_from_cache()
      except:
        print("Failed to fetch {} from cache (ignoring)".format(self.cache_key))
        traceback.print_exc()

      # Branch based on fetched.
      if self.install_is_ok():
        # Fetch succeeded. No deps.
        return
      else:
        # Fetch did not succeed. Delegate to the install task.
        print("Could not fetch cached {}: Building locally".format(
            self.identifier))
        return {
            "task_dep": [subtask("store_cache", qualified=True),],
        }

    def store_cache():
      try:
        self.store_install_to_cache()
      except:
        print("Error installing {} to cache (skipping cache)".format(
            self.cache_key))
        traceback.print_exc()
      else:
        self.touch_marker_file()

    # Main task that delegates dep calculation to fetch_cache.
    yield {
        "name": basename,
        "actions": None,
        "calc_dep": [subtask("fetch_cache", qualified=True)]
    }
    yield {
        "name": subtask("fetch_cache"),
        "actions": [fetch_cache],
    }
    yield {
        "name": subtask("store_cache"),
        "actions": [store_cache],
        "task_dep": [self.install_task],
    }
