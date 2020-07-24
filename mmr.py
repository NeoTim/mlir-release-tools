#!/usr/bin/env python3
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
"""Automatically fetches and launches into an .mmrepo directory.

This script can be put in the root directory of a git repo, and once
downloaded, will act as a call to the main entry point.
"""

import os
import urllib.request
import sys
from zipfile import ZipFile

MMR_ZIP_URL = "https://github.com/google/git-mmrepo/archive/main.zip"
THIS_DIR = os.path.dirname(__file__)
ARCHIVE_PATH = os.path.join(THIS_DIR, ".mmrepo", "mmr_dist.zip")
DIST_DIR = os.path.join(THIS_DIR, ".mmrepo", "mmr_dist")

if not os.path.exists(DIST_DIR):
  os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)
  print("Fetching {} to {}...".format(MMR_ZIP_URL, ARCHIVE_PATH),
        file=sys.stderr)
  with urllib.request.urlopen(MMR_ZIP_URL) as infile:
    with open(ARCHIVE_PATH, "wb") as outfile:
      outfile.write(infile.read())
  os.makedirs(DIST_DIR, exist_ok=True)
  with ZipFile(ARCHIVE_PATH, "r") as zf:
    zf.extractall(path=DIST_DIR)

sys.path.insert(0, os.path.join(DIST_DIR, "git-mmrepo-main", "python"))
from mmrepo import main
main.main()
