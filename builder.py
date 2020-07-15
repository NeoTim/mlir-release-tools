"""Utilities for invoking builds."""

from pathlib import *
import json
import os
import shutil
import subprocess

TOP_DIR = Path.cwd()
DEFAULT_BUILD_ROOT = TOP_DIR.joinpath("build").resolve()
DEFAULT_INSTALL_ROOT = TOP_DIR.joinpath("install").resolve()


def get_build_root():
  return DEFAULT_BUILD_ROOT


def get_install_root():
  return DEFAULT_INSTALL_ROOT


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

  @staticmethod
  def load(*, config_file, **kwargs):
    with open(config_file, "rt") as f:
      d = json.load(f)
    build_type = "cmake" if "build_type" not in d else d["build_type"]
    if build_type == "cmake":
      return CMakeBuildConfig(json_dict=d, **kwargs)
    else:
      raise ValueError("Bad 'build_type' = {} in {}".format(
          build_type, config_file))

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


class CMakeBuildConfig(BuildConfig):
  """CMake specific build config."""

  def __init__(self, configure_dir=None, **kwargs):
    super().__init__(**kwargs)
    self.configure_dir = (self.source_dir
                          if configure_dir is None else configure_dir)

  def _exec_cmake(self, cmake_args):
    cmake_args = [str(c) for c in cmake_args]
    print("++ EXEC:", " ".join(cmake_args))
    subprocess.check_call(cmake_args, cwd=self.build_dir)

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

  def clean(self):
    """Cleans build and install directories."""
    shutil.rmtree(self.install_dir)
    shutil.rmtree(self.build_dir)

