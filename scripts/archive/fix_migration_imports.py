import os
path = r"backend\alembic\versions\210020910165_add_missing_tables.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
lines.insert(9, "import pgvector.sqlalchemy\n")
lines.insert(9, "from sqlalchemy.dialects import postgresql\n")
with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("Added missing imports")
