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

import os
from pathlib import *
import shutil
import subprocess
import sys

import builder
import cacher
import pythonenv

__all__ = [
    "task_iree_python_deps",
    "task_iree_default",
    "task_iree_tf_default",
]

LLVM_CONFIG = "mlir-generic-rtti"


def get_src_dir():
  return builder.TOP_DIR.joinpath("external/iree")


def get_llvm_install_dir():
  return builder.get_install_root().joinpath("llvm-project", LLVM_CONFIG)


def get_base_cmake_config():
  llvm_install_path = get_llvm_install_dir().joinpath("lib/cmake/mlir")
  config = dict(BASE_CMAKE_PROTOTYPE)
  add_cmake_args(config, "-DMLIR_DIR={}".format(llvm_install_path))
  return config


def get_manylinux_platform():
  """Gets the manylinux platform.

  This can also be used to check if building under manylinux since the env
  var implies this and also implies the presence of the auditwheel tool.
  """
  return os.environ.get("AUDITWHEEL_PLAT")


def task_iree_python_deps():
  """Installs required deps for all python versions."""
  def deps():
    pythonenv.pip_install("absl-py", "numpy")

  return {
      "actions": [(deps, [])],
  }


################################################################################
# CMake build
################################################################################

BASE_CMAKE_PROTOTYPE = {
    "canonical_cmake_args": [
        "-DIREE_BUILD_PYTHON_BINDINGS=ON",
        "-DIREE_BUILD_SAMPLES=OFF",
        "-DIREE_MLIR_DEP_MODE=INSTALLED",
        "-DIREE_HAL_DRIVERS_TO_BUILD=DyLib;Vulkan;VMLA",
    ]
}


def add_cmake_args(config, *args):
  config["canonical_cmake_args"].extend(args)


def get_python_cmake_config():
  config = get_base_cmake_config()
  python_exe = sys.executable
  add_cmake_args(config, "-DIREE_BUILD_PYTHON_BINDINGS=ON",
                 "-DPYTHON_EXECUTABLE={}".format(python_exe))

  # Add CMake vars for python configs.
  python_configs = pythonenv.get_python_target_configs()
  config_idents = []
  for python_config in python_configs:
    ident = python_config.ident
    config_idents.append(ident)
    add_cmake_args(
        config,
        "-DIREE_MULTIPY_{}_EXECUTABLE='{}'".format(ident, python_config.exe),
        "-DIREE_MULTIPY_{}_INCLUDE_DIRS='{}'".format(
            ident, ";".join(python_config.include_dirs)),
        "-DIREE_MULTIPY_{}_LIBRARIES='{}'".format(
            ident, ";".join(python_config.libraries)),
        "-DIREE_MULTIPY_{}_EXTENSION='{}'".format(ident,
                                                  python_config.extension))
  add_cmake_args(config,
                 "-DIREE_MULTIPY_VERSIONS='{}'".format(";".join(config_idents)))
  return config


def task_iree_default():
  """Builds the IREE default configration."""
  taskname = "iree_default"
  config = get_python_cmake_config()
  bc = builder.CMakeBuildConfig(identifier=taskname,
                                source_dir=get_src_dir(),
                                json_dict=config)
  yield bc.yield_tasks(taskname=taskname,
                       install_target="install",
                       task_dep=["llvm:" + LLVM_CONFIG])

  # Generate python wheel targets.
  python_configs = pythonenv.get_python_target_configs()
  for python_config in python_configs:
    yield distribute_pyiree(taskname=taskname,
                            label="pyiree_{}".format(python_config.ident),
                            python_config=python_config,
                            src_dir=bc.source_dir,
                            build_dir=bc.build_dir,
                            install_dir=bc.install_dir)


def distribute_pyiree(taskname, label, python_config, src_dir, build_dir,
                      install_dir):
  """Creates tasks to install pyiree."""
  pyiree_build_dir = builder.get_build_root().joinpath("{}_{}".format(
      taskname, label))
  packaging_src_dir = Path(src_dir).joinpath("packaging/python")
  dist_wheel_dir = Path(install_dir).joinpath("dist/{}".format(label))

  def install_wheels(setup_dir):
    os.makedirs(dist_wheel_dir, exist_ok=True)
    for file in setup_dir.joinpath("dist").glob("*.whl"):
      dist_wheel_file = dist_wheel_dir.joinpath(file.name)
      shutil.copy(file, dist_wheel_file)
      # Run auditwheel as needed.
      if pythonenv.is_manylinux_image():
        print("Running auditwheel on", dist_wheel_file)
        builder.subcommand(["auditwheel", "repair",
                            str(dist_wheel_file)],
                           cwd=dist_wheel_dir)
        os.remove(dist_wheel_file)

  def setup(setup_py):
    setup_dir = pyiree_build_dir.joinpath(setup_py)
    shutil.rmtree(setup_dir, ignore_errors=True)
    os.makedirs(setup_dir, exist_ok=True)
    args = [
        python_config.exe,
        packaging_src_dir.joinpath(setup_py),
        "bdist_wheel",
    ]
    builder.subcommand(args,
                       env={
                           "PYIREE_CMAKE_BUILD_ROOT": build_dir,
                       },
                       cwd=setup_dir)
    install_wheels(setup_dir)

  yield {
      "name": label,
      "actions": [
          (setup, ["setup_compiler.py"]),
          (setup, ["setup_rt.py"]),
      ],
      "task_dep": [taskname + ":install"],
  }


################################################################################
# Bazel build
################################################################################


def get_bazel_python_build_flags(python_config):
  opt_flags = [
      "--compilation_mode=opt",
  ]
  disk_cache_path = cacher.get_cache_root().joinpath(".bazelcache")
  cache_flags = [
      "--disk_cache={}".format(disk_cache_path),
  ]
  return [
      "--config=generic_gcc",
      # Python binaries.
      # TODO: Why do we need three of these?
      "--python_path={}".format(python_config.exe),
      "--action_env",
      "PYTHON_BIN={}".format(python_config.exe),
      "--action_env",
      "PYTHON_BIN_PATH={}".format(python_config.exe),
      # Addl flags.
      # On RHEL6/Centos6 (manylinux2014), post-release additions to the C++
      # standard library are included in an auxillary static library.
      "--action_env",
      "BAZEL_LINKLIBS=-l%:libstdc++.a",
  ] + opt_flags + cache_flags


def task_iree_tf_default():
  """Builds the IREE tensorflow default configuration.

  Note that this all has to be done sequentially (versus as tasks with deps)
  because we have to re-use the build directory to incrementally build
  for successively different python versions.
  """
  build_dir = builder.get_build_root().joinpath("iree_tf_bazel")
  python_build_dir = build_dir.joinpath("python")
  os.makedirs(build_dir, exist_ok=True)
  install_dir = builder.get_install_root().joinpath("iree_tf")
  packaging_src_dir = get_src_dir().joinpath("packaging", "python")

  # Pick an appropriate bazel-out.
  output_base = os.environ.get("BAZEL_OUTPUT_BASE")
  if output_base is None:
    output_base = build_dir.joinpath("bazel-out")

  def exec_build(python_config, flags):
    dist_wheel_dir = install_dir.joinpath("dist/{}".format(python_config.ident))
    os.makedirs(dist_wheel_dir, exist_ok=True)

    # invoke the bazel build.
    bazel_args = [
        "bazel",
        "--output_base={}".format(output_base),
        "build",
        # TODO: Debug sandbox perf issues.
        # "--spawn_strategy=standalone",
    ] + flags + [
        "//packaging/python:all_pyiree_packages",
    ]
    builder.subcommand(bazel_args, cwd=get_src_dir())

    # Now, using the identified python, copy from the runfiles to a proper
    # python path layout (normalizing filenames in a way that bazel can't do).
    builder.subcommand([
        python_config.exe,
        packaging_src_dir.joinpath("hack_python_package_from_runfiles.py"),
        python_build_dir
    ],
                       cwd=get_src_dir())

    # Invoke setup.
    # Outputs into setup_dir.
    setup_dir = build_dir.joinpath("pyiree_setup_tf")
    shutil.rmtree(setup_dir, ignore_errors=True)
    os.makedirs(setup_dir, exist_ok=True)
    args = [
        python_config.exe,
        packaging_src_dir.joinpath("setup_tf.py"),
        "bdist_wheel",
    ]
    builder.subcommand(args,
                       cwd=setup_dir,
                       env={
                           "PYIREE_PYTHON_ROOT": python_build_dir,
                       })

    # Copy each built wheel to the dist directory.
    for wheel_file in setup_dir.joinpath("dist").glob("*.whl"):
      dist_wheel_file = dist_wheel_dir.joinpath(wheel_file.name)
      shutil.copy(wheel_file, dist_wheel_file)
      # Run auditwheel as needed.
      if pythonenv.is_manylinux_image():
        print("Running auditwheel on", dist_wheel_file)
        builder.subcommand(["auditwheel", "repair",
                            str(dist_wheel_file)],
                           cwd=dist_wheel_dir)
        os.remove(dist_wheel_file)

  python_configs = pythonenv.get_python_target_configs()
  for python_config in python_configs:
    yield {
        "name": ("build-" + python_config.ident),
        "actions": [
            (exec_build,
             [python_config,
              get_bazel_python_build_flags(python_config)])
        ],
    }

    # TODO: Enable all of the python configs once stable.
    break
