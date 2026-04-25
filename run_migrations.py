#!/usr/bin/env python
"""Run Alembic migrations with environment variables loaded."""
import os
import subprocess
import sys
from pathlib import Path

# Load .env.local
env_file = Path(".env.local")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip().strip("'\"")

# Change to backend directory
os.chdir("backend")

# Run alembic with the loaded environment
result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    env=os.environ
)
sys.exit(result.returncode)
