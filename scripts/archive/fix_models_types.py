import re
from pathlib import Path

models_dir = Path("backend/shared/db/models")

for py_file in models_dir.glob("*.py"):
    if py_file.name == "__pycache__":
        continue
    content = py_file.read_text(encoding="utf-8")
    
    # Replace PG_UUID(as_uuid=False) with String(36)
    content = content.replace("PG_UUID(as_uuid=False)", "String(36)")
    content = content.replace("PG_UUID", "String(36)")
    content = content.replace("UUID(as_uuid=True)", "String(36)")
    
    # Ensure String is imported
    if "String(36)" in content and "from sqlalchemy import" in content and "String" not in content.split("from sqlalchemy import")[1].split("\n")[0]:
        content = content.replace("from sqlalchemy import ", "from sqlalchemy import String, ")
        
    py_file.write_text(content, encoding="utf-8")
    print(f"Fixed {py_file.name}")
