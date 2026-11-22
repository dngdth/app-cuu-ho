"""Run browser tests and always remove only their verified temporary DB schema."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
env = {**os.environ, "E2E_PYTHON": sys.executable}
try:
    command = shutil.which("npx.cmd" if os.name == "nt" else "npx")
    result = subprocess.run([command, "playwright", "test"], cwd=root / "fe", env=env)
finally:
    subprocess.run([sys.executable, str(root / "test/e2e_server.py"), "--cleanup"], cwd=root, check=True)
raise SystemExit(result.returncode)
