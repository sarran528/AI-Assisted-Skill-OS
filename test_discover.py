#!/usr/bin/env python
"""Quick test to debug template discovery."""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    from backend.skill.template_pipeline import SkillTemplatePipeline
    
    pipeline = SkillTemplatePipeline(db_session=None)
    try:
        skill_name = "java"
        print(f"\nAttempting to discover skill: {skill_name}\n")
        
        result = await pipeline.build_with_fallback(skill_name)
        
        if result:
            print(f"\nSUCCESS! Generated template:")
            print(f"   Version: {result.version}")
            print(f"   Phases: {list(result.template.get('phases', {}).keys())}")
        else:
            print(f"\nFAILED - pipeline returned None")
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
