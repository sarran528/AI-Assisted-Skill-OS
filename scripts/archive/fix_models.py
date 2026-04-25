#!/usr/bin/env python
"""Fix all model files for SQLite compatibility."""
import re
from pathlib import Path

models_dir = Path("backend/shared/db/models")

for py_file in models_dir.glob("*.py"):
    if py_file.name == "__pycache__":
        continue
    
    content = py_file.read_text()
    original = content
    
    # Fix imports - add datetime and uuid4
    if "from sqlalchemy import" in content and "from datetime import" not in content:
        # Add import for datetime
        lines = content.split("\n")
        import_idx = next(i for i, line in enumerate(lines) if "from sqlalchemy import" in line)
        if "from datetime import" not in "\n".join(lines[:import_idx]):
            lines.insert(import_idx, "from datetime import datetime")
            lines.insert(import_idx + 1, "from uuid import uuid4")
            content = "\n".join(lines)
    
    # Fix UUID imports
    content = re.sub(
        r"from sqlalchemy\.dialects\.postgresql import (.+)",
        lambda m: _fix_import(m.group(1)),
        content
    )
    
    # Fix UUID column definitions
    content = re.sub(
        r"Column\(UUID\(as_uuid=True\)",
        r"Column(PG_UUID(as_uuid=False), default=lambda: str(uuid4())",
        content
    )
    
    # Fix JSONB to JSON
    content = re.sub(r"\bJSONB\b", "JSON", content)
    
    # Fix INET (IP address) to String
    content = re.sub(r", INET,", ", String(45),", content)
    content = re.sub(r"Column\(INET,", "Column(String(45),", content)
    
    if content != original:
        py_file.write_text(content)
        print(f"✓ Fixed {py_file.name}")
    else:
        print(f"  Skipped {py_file.name}")

def _fix_import(imports_str):
    """Fix PostgreSQL specific imports."""
    imports = [i.strip() for i in imports_str.split(",")]
    new_imports = []
    added_uuid = False
    
    for imp in imports:
        if imp == "UUID":
            if not added_uuid:
                new_imports.append("UUID as PG_UUID")
                added_uuid = True
        elif imp != "JSONB":  # Remove JSONB, we use JSON
            new_imports.append(imp)
    
    if not added_uuid and "UUID" in imports_str:
        new_imports.append("UUID as PG_UUID")
    
    return f"from sqlalchemy.dialects.postgresql import {', '.join(new_imports)}"

print("\nDone!")
