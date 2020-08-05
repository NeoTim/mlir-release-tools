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
import pathlib
import shutil
import sys

# Add the python/ directory to the path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))

# Local deps.
import builder
import cacher
import pythonenv

# Sub-tasks.
from common_tasks import *
from llvm_tasks import *
from iree_tasks import *
from npcomp_tasks import *

DOIT_CONFIG = {
    "default_tasks": [],
}


def task_envinfo():
  """Displays information about the python build environment."""
  def print_info():
    configs = pythonenv.get_python_target_configs()
    print("Cache directory:", cacher.get_cache_root())
    print("Python build target configs:")
    for config in configs:
      print(" ", config)

  return {
    "actions": [(print_info, [])],
    "uptodate": [False],
    "verbosity": 2,
  }
