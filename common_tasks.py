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

__all__ = [
    "task_envinfo",
    "task_llvm",
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


def task_llvm():
  """Configures and builds LLVM configurations from the llvm-configs/ dir.

  Note that this is a group task covering all LLVM configurations. Individual
  configs are depended on via llvm:{config-name}.

  There will be several sub-tasks:
    :config
    :build
    :install
  """
  suffix = ".config.json"
  config_files = builder.TOP_DIR.joinpath("llvm-configs").glob("*" + suffix)
  for config_file in config_files:
    config_name = config_file.name[0:-len(suffix)]
    source_dir = builder.TOP_DIR.joinpath("external/llvm-project")
    bc = builder.CMakeBuildConfig.load(
        identifier="llvm-project/{}".format(config_name),
        config_file=config_file,
        source_dir=source_dir,
        configure_dir=source_dir.joinpath("llvm"))
    yield bc.yield_tasks(
      taskname="llvm",
      basename=config_name,
      install_target="install")

def task_pybind11():
  """Installs pybind11."""
  bc = builder.CMakeBuildConfig(
      identifier="pybind11",
      source_dir=builder.TOP_DIR.joinpath("external/pybind11"),
      json_dict={"canonical_cmake_args": []})
  yield bc.yield_tasks(taskname="pybind11", install_target="install")
