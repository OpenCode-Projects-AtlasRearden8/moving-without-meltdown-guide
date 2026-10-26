"""Pytest configuration.

Builds the site once before any test runs, so tests always verify a
fresh build rather than leftovers from a previous one.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(HERE, "build.py")


def pytest_configure(config):
    subprocess.run([sys.executable, BUILD, "--quiet"], cwd=HERE, check=True)
