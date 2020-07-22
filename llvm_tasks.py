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
    "task_llvm",
    "task_build_llvm",
]


def _get_configs():
  """Gets the (config_name, config_file, identifier) tuples of LLVM configs."""
  suffix = ".config.json"
  for config_file in builder.TOP_DIR.joinpath("llvm-configs").glob("*" +
                                                                   suffix):
    config_name = config_file.name[0:-len(suffix)]
    identifier = "llvm-project/{}".format(config_name)
    yield config_name, config_file, identifier


def _get_source_dir():
  return builder.TOP_DIR.joinpath("external/llvm-project")


def task_llvm():
  """Installs a cached LLVM build or builds locally."""
  for config_name, config_file, identifier in _get_configs():
    ic = cacher.InstallCache(
        identifier=identifier,
        cache_key="llvm-project__{}".format(config_name),
        install_task="build_llvm:{}:install".format(config_name),
        version_data_lambda=lambda: cacher.read_git_state(_get_source_dir()))
    yield ic.yield_tasks(taskname="llvm", basename=config_name)


def task_build_llvm():
  """Configures and builds LLVM configurations from the llvm-configs/ dir.

  Note that this is a group task covering all LLVM configurations. Individual
  configs are depended on via build_llvm:{config-name}.

  There will be several sub-tasks:
    :config
    :build
    :install
  """
  for config_name, config_file, identifier in _get_configs():
    source_dir = _get_source_dir()
    bc = builder.CMakeBuildConfig.load(
        identifier=identifier,
        config_file=config_file,
        source_dir=source_dir,
        configure_dir=source_dir.joinpath("llvm"))
    yield bc.yield_tasks(taskname="build_llvm",
                         basename=config_name,
                         install_target="install")
