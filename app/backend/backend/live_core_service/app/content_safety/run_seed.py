import asyncio
from app.database import get_db
from app.content_safety.seed import seed_default_rules


async def run():
    async for db in get_db():
        result = await seed_default_rules(db)
        print(f"Seed complete: {result} rules")
        break


asyncio.run(run())
