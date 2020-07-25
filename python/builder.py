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

"""Utilities for invoking builds."""

from pathlib import *
import json
import os
import shutil
import subprocess
import sys

TOP_DIR = Path.cwd()
DEFAULT_BUILD_ROOT = TOP_DIR.joinpath("build").resolve()
DEFAULT_INSTALL_ROOT = TOP_DIR.joinpath("install").resolve()


def get_build_root():
  return DEFAULT_BUILD_ROOT


def get_install_root():
  return DEFAULT_INSTALL_ROOT


def subcommand(args, cwd, env=None):
  if env is not None:
    sub_env = dict(os.environ)
    sub_env.update(env)
    env = sub_env
  args = [str(c) for c in args]
  print("++ EXEC:", " ".join(args))
  subprocess.check_call(args, cwd=cwd, env=env)


class BuildConfig:
  """Wraps a JSON build configuration.

  The base class delegates based on the 'build_type' key.
  """

  def __init__(self, *, identifier, json_dict, source_dir):
    super().__init__()
    self.identifier = identifier
    self.json_dict = json_dict
    self.source_dir = source_dir

  def __repr__(self):
    return "BuildConfig({}, {})".format(self.identifier, self.json_dict)

  @classmethod
  def load(cls, *, config_file, **kwargs):
    with open(config_file, "rt") as f:
      d = json.load(f)
    return cls(json_dict=d, **kwargs)

  @property
  def build_dir(self):
    """Gets the build directory for this config."""
    path = get_build_root().joinpath(self.identifier)
    os.makedirs(path, exist_ok=True)
    return path

  @property
  def install_dir(self):
    """Gets the install directory for this config."""
    path = get_install_root().joinpath(self.identifier)
    os.makedirs(path, exist_ok=True)
    return path

  def yield_tasks(self):
    """Yields tasks for the build."""
    raise NotImplementedError()


class CMakeBuildConfig(BuildConfig):
  """CMake specific build config."""

  def __init__(self, configure_dir=None, **kwargs):
    super().__init__(**kwargs)
    self.configure_dir = Path(
        self.source_dir if configure_dir is None else configure_dir)

  def yield_tasks(self,
                  *,
                  taskname=None,
                  basename=None,
                  install_target=None,
                  task_dep=()):
    """Performs a CMake build."""

    def clean_build():
      shutil.rmtree(self.build_dir)

    def clean_install():
      shutil.rmtree(self.install_dir)

    def subtask(suffix, qualified=False):
      subtask_name = basename + ":" + suffix if basename is not None else suffix
      if qualified and taskname is not None:
        return taskname + ":" + subtask_name
      else:
        return subtask_name

    # "Group" task that depends on individual tasks.
    yield {
        "name": basename,
        "actions": None,
        "task_dep": [subtask("install", qualified=True),],
    }

    # Configure task.
    yield {
        "name": subtask("config"),
        "actions": [(self.configure, [])],
        "targets": [self.build_dir.joinpath("CMakeCache.txt")],
        "file_dep": [self.configure_dir.joinpath("CMakeLists.txt")],
        "clean": [clean_build],
        "task_dep": list(task_dep),
    }
    # Build task.
    yield {
        "name": subtask("build"),
        "actions": [(self.build, ["all"])],
        "file_dep": [self.build_dir.joinpath("CMakeCache.txt")],
        "clean": [clean_build],
        "task_dep": [subtask("config", qualified=True)],
    }
    # Install.
    if install_target:
      yield {
          "name": subtask("install"),
          "actions": [(self.build, [install_target])],
          "file_dep": [self.build_dir.joinpath("CMakeCache.txt")],
          "clean": [clean_install],
          "task_dep": [subtask("build", qualified=True)],
      }
    else:
      yield {
          "name": subtask("install"),
          "actions": None,
          "task_dep": [subtask("build", qualified=True)],
      }

  def _exec_cmake(self, cmake_args):
    subcommand(cmake_args, cwd=self.build_dir)

  @property
  def canonical_cmake_args(self):
    """Gets the list of canonical cmake args from the config."""
    value = self.json_dict.get("canonical_cmake_args")
    return value if value else []

  def configure_and_build(self, extra_configure_args=(), targets=()):
    self.configure(extra_args=extra_configure_args)
    self.build(targets=targets)

  def configure(self, extra_args=()):
    """Configures the component."""
    build_dir = self.build_dir
    cmake_args = [
        # TODO: Pull these out to common cmake args.
        "cmake",
        "-GNinja",
        "-S{}".format(self.configure_dir),
        "-B{}".format(build_dir),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX={}".format(self.install_dir),
    ] + self.canonical_cmake_args + list(extra_args)
    self._exec_cmake(cmake_args)

  def build(self, *targets):
    """Builds the component."""
    build_dir = self.build_dir
    cmake_args = [
        "cmake",
        "--build",
        build_dir,
    ]
    for target in targets:
      cmake_args.extend(["--target", target])
    self._exec_cmake(cmake_args)
