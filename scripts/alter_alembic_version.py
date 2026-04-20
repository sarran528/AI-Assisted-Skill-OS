import os
from pathlib import Path

import asyncpg


def load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing env file: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


async def main() -> None:
    load_env(Path(".env.local"))
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not found in .env.local")

    url = url.replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)
    try:
        await conn.execute(
            "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)"
        )
    finally:
        await conn.close()

    print("Updated alembic_version.version_num to VARCHAR(64)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
