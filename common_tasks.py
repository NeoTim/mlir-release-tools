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

import builder
import cacher

__all__ = [
    "task_envinfo",
    "task_pybind11",
]


def task_envinfo():
  """Prints information about the environment."""

  def print_envinfo():
    print("BUILD_ROOT:", builder.get_build_root())
    print("INSTALL_ROOT:", builder.get_install_root())

  return {
      "actions": [print_envinfo],
      "uptodate": [False],
      "verbosity": 2,
  }


def task_pybind11():
  """Installs pybind11."""
  bc = builder.CMakeBuildConfig(
      identifier="pybind11",
      source_dir=builder.TOP_DIR.joinpath("external/pybind11"),
      json_dict={"canonical_cmake_args": []})
  yield bc.yield_tasks(taskname="pybind11", install_target="install")
