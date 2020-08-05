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

import sys

import builder
import cacher
import pythonenv

LLVM_CONFIG = "mlir-generic-rtti"

__all__ = [
    "task_npcomp_default",
]


def get_src_dir():
  return builder.TOP_DIR.joinpath("external", "mlir-npcomp")


def get_llvm_lit_path():
  lit_path = builder.TOP_DIR.joinpath("external", "llvm-project", "llvm",
                                      "utils", "lit", "lit.py")
  assert lit_path.exists(), "Could not find lit ({})".format(lit_path)
  return lit_path


def get_llvm_install_dir():
  return builder.get_install_root().joinpath("llvm-project", LLVM_CONFIG)


def get_pybind11_install_dir():
  return builder.get_install_root().joinpath("pybind11")


################################################################################
# CMake build
################################################################################

BASE_CMAKE_PROTOTYPE = {"canonical_cmake_args": ["-DLLVM_ENABLE_WARNINGS=ON",]}


def add_cmake_args(config, *args):
  config["canonical_cmake_args"].extend(args)


def get_base_cmake_config():
  llvm_install_path = get_llvm_install_dir().joinpath("lib/cmake/mlir")
  config = dict(BASE_CMAKE_PROTOTYPE)
  add_cmake_args(
      config,  # Base args
      "-DMLIR_DIR={}".format(llvm_install_path),
      "-Dpybind11_DIR={}".format(
          get_pybind11_install_dir().joinpath("share/cmake/pybind11")),
      "-DLLVM_EXTERNAL_LIT={}".format(get_llvm_lit_path()))
  return config


def get_python_cmake_config():
  config = get_base_cmake_config()

  python_configs = pythonenv.get_python_target_configs()
  for python_config in python_configs:
    add_cmake_args(
        config,  # Python args
        "-DPYTHON_EXECUTABLE={}".format(python_config.exe),
        "-DPYTHON_LIBRARIES={}".format(";".join(python_config.libraries)),
        "-DPYTHON_INCLUDE_DIRS={}".format(";".join(python_config.include_dirs)),
        "-DPYTHON_MODULE_PREFIX=",
        "-DPYTHON_MODULE_EXTENSION={}".format(python_config.extension))
    if not python_config.libraries:
      # Disable version-specific shared linkage if the python environment
      # does not report libraries to link against (avoids a race where the
      # CMake python configuration "tries harder" to find libraries, but we
      # need to respect what the environment reports for distribution).
      add_cmake_args(config, "-DNPCOMP_PYTHON_BINDINGS_VERSION_LOCKED=0")

    # TODO: Enable multiple python configs
    break
  return config


def task_npcomp_default():
  """A default build of npcomp."""
  taskname = "npcomp_default"
  config = get_python_cmake_config()
  bc = builder.CMakeBuildConfig(identifier=taskname,
                                source_dir=get_src_dir(),
                                json_dict=config)
  yield bc.yield_tasks(taskname=taskname,
                       install_target="install",
                       test_target="check-npcomp",
                       task_dep=[
                           "llvm:" + LLVM_CONFIG,
                           "pybind11:default",
                       ])
