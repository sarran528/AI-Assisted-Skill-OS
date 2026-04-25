import re
from pathlib import Path

models_dir = Path("backend/shared/db/models")

for py_file in models_dir.glob("*.py"):
    if py_file.name == "__pycache__":
        continue
    content = py_file.read_text(encoding="utf-8")
    
    # Replace the broken import
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if "from sqlalchemy.dialects.postgresql import" in line and "String(36)" in line:
            # Check if there are other imports on the same line
            parts = line.split("import ")[1].split(",")
            clean_parts = [p.strip() for p in parts if "String(36)" not in p]
            if clean_parts:
                new_lines.append(f"from sqlalchemy.dialects.postgresql import {', '.join(clean_parts)}")
        else:
            new_lines.append(line)
            
    py_file.write_text('\n'.join(new_lines), encoding="utf-8")
    print(f"Cleaned {py_file.name}")
