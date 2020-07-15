import builder
import os
import pathlib
import shutil

DOIT_CONFIG = {
    "default_tasks": [],
}


def relative_path(local_path):
  top_dir = pathlib.Path(os.path.dirname(__file__))
  local_path = pathlib.Path(local_path)
  return top_dir.joinpath(local_path)


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
  """Configures and builds LLVM configurations from the llvm-configs/ dir."""

  suffix = ".config.json"
  config_files = relative_path("llvm-configs").glob("*" + suffix)
  for config_file in config_files:
    config_name = config_file.name[0:-len(suffix)]
    source_dir = builder.TOP_DIR.joinpath("external/llvm-project")
    bc = builder.BuildConfig.load(
        identifier="llvm-project/{}".format(config_name),
        config_file=config_file,
        source_dir=source_dir,
        configure_dir=source_dir.joinpath("llvm"))
    yield {
        "name": config_name,
        "actions": [
            (bc.configure, []),
            (bc.build, ["install"]),
        ],
        "targets": [bc.build_dir, bc.install_dir],
        "clean": [bc.clean],
    }


def task_pybind11():
  """Installs pybind11."""
  bc = builder.CMakeBuildConfig(
      identifier="pybind11",
      source_dir=builder.TOP_DIR.joinpath("external/pybind11"),
      json_dict={"canonical_cmake_args": []})
  return {
      "actions": [
          (bc.configure, []),
          (bc.build, ["install"]),
      ],
      "targets": [bc.build_dir, bc.install_dir],
      "clean": [bc.clean],
  }
