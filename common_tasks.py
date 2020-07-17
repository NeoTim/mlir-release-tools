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
