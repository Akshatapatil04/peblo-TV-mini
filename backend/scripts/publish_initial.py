import asyncio
from backend.app.services.publisher import execute_publish
from backend.app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        result = await execute_publish(session, initiated_by="admin", force=True)
        print(f"[SUCCESS] Initial catalogue published: Version={result['version']}, Shows={result['shows_count']}, Episodes={result['episodes_count']}")

if __name__ == "__main__":
    asyncio.run(main())
