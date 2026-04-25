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

print("Generating missing tables migration...")
result = subprocess.run(
    [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "add_missing_tables"],
    env=os.environ
)

if result.returncode == 0:
    print("\nApplying migration...")
    result2 = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=os.environ
    )
    sys.exit(result2.returncode)
else:
    sys.exit(result.returncode)
print("STDOUT:", res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)

if res.returncode != 0:
    print("Failed to generate migration")
    sys.exit(1)

print("\nApplying migration...")
res2 = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    env=env,
    capture_output=True,
    text=True
)
print("STDOUT:", res2.stdout)
if res2.stderr:
    print("STDERR:", res2.stderr)
