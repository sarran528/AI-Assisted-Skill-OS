#!/usr/bin/env python
"""Test the skill discovery API endpoint."""

import asyncio
import httpx
import json

async def main():
    """Test /skills/discover endpoint."""
    async with httpx.AsyncClient() as client:
        url = "http://localhost:8000/api/v1/skill/discover"
        
        payload = {
            "skill_name": "java",
            "domain": "other",
            "complexity_score": 0.5
        }
        
        print(f"Testing endpoint: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print()
        
        try:
            response = await client.post(
                url,
                json=payload,
                timeout=120.0,  # Long timeout for LLM calls
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except httpx.ConnectError:
            print("ERROR: Cannot connect to backend at localhost:8000")
            print("Is the backend running? Try: python -m uvicorn backend.main:app --reload")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
