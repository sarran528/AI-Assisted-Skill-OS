"""
Seed script to populate skill templates into database.
Reads JSON files from data/skill_templates/ and inserts them.

Usage:
    python -m scripts.seed_skills
"""

import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.shared.config import settings
from backend.shared.db.models import SkillTemplate
from backend.shared.db.repositories.skill_template_repository import (
    SkillTemplateRepository,
)
from backend.skill.template_schema import validate_template_structure


async def seed_skills():
    """Load and insert skill templates from JSON files."""
    
    # Set up async database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )
    
    # Create async session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Get path to skill templates directory
    templates_dir = Path(__file__).parent.parent / "data" / "skill_templates"
    
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return
    
    # Find all JSON files
    json_files = sorted(templates_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {templates_dir}")
        return
    
    print(f"📚 Found {len(json_files)} skill template files")
    
    async with async_session() as session:
        repo = SkillTemplateRepository(session)
        
        for json_file in json_files:
            print(f"\n📖 Processing {json_file.name}...")
            
            try:
                # Read JSON file
                with open(json_file, "r") as f:
                    data = json.load(f)
                
                # Validate structure
                validate_template_structure(data["structure"])
                
                # Check if skill already exists
                existing = await repo.get_active_template(data["skill_id"])
                
                if existing:
                    print(f"   ✓ Skill '{data['skill_id']}' already exists (version {existing.version})")
                    continue
                
                # Create skill template
                template = await repo.create_template(data)
                
                print(f"   ✅ Created '{data['skill_id']}' (v{template.version})")
                print(f"      - Name: {data['name']}")
                print(f"      - Domain: {data['domain']}")
                print(f"      - Complexity: {data['complexity_score']}")
                print(f"      - Phases: {', '.join(data['structure']['phases'].keys())}")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing error: {e}")
            except ValueError as e:
                print(f"   ❌ Validation error: {e}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print("\n✨ Seeding complete!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_skills())
