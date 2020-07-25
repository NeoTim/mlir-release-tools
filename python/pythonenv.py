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
"""Queries information about the python build environment."""

from collections import namedtuple
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

_PYTHON_TARGET_CONFIGS = None

_PYTHON_CONFIG_SCRIPT = r"""
import json
import sys
import sysconfig
d = dict()
configs = d["configs"] = list()
exe = sys.executable
print(json.dumps({
    "ident": sysconfig.get_config_var("SOABI"),
    "exe": exe,
    "include_dirs": [sysconfig.get_config_var("INCLUDEPY")],
    # Manylinux does not link against libraries.
    "libraries": [],
    "extension": sysconfig.get_config_var("EXT_SUFFIX"),
}))
"""


class PythonTargetConfig(
    namedtuple("PythonTargetConfig",
               "ident,exe,include_dirs,libraries,extension")):
  pass


def get_python_target_configs():
  """Gets a list of PythonTargetConfig for building."""

  def query_manylinux_config():
    configs = []
    _, tmpscript = tempfile.mkstemp(".py")
    try:
      with open(tmpscript, "wt") as f:
        f.write(_PYTHON_CONFIG_SCRIPT)
      for exe in _get_manylinux_python_exes():
        config_str = subprocess.check_output([exe, tmpscript]).decode("UTF-8")
        config_dict = json.loads(config_str)
        configs.append(PythonTargetConfig(**config_dict))
    finally:
      os.remove(tmpscript)
    return tuple(configs)

  def query_config():
    if is_manylinux_image():
      return query_manylinux_config()
    # Just return a config based on this instance.
    ldlibpath = sysconfig.get_config_var("LD")
    ldlib = sysconfig.get_config_var("LDLIBRARY")
    return tuple([
        PythonTargetConfig(
            ident="default",
            exe=sys.executable,
            include_dirs=[sysconfig.get_config_var("INCLUDEPY")],
            libraries=[
                ldlib if not ldlibpath else os.path.join(ldlibpath, ldlib)
            ],
            extension=sysconfig.get_config_var("EXT_SUFFIX")),
    ])

  global _PYTHON_TARGET_CONFIGS
  if _PYTHON_TARGET_CONFIGS is None:
    _PYTHON_TARGET_CONFIGS = query_config()
  return _PYTHON_TARGET_CONFIGS


def _get_manylinux_python_exes():
  """Gets the 'python' executables for all installed manylinux versions."""
  PYTHON_PARENT_PATH = Path("/opt/python")
  return reversed(sorted(PYTHON_PARENT_PATH.glob("*/bin/python")))


def is_manylinux_image():
  """Determine whether running on a manylinux image."""
  return os.environ.get("AUDITWHEEL_PLAT") and _get_manylinux_python_exes()
