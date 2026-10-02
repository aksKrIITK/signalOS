import asyncio
import asyncpg
from app.db.database import engine
from app.main import seed_initial_data

async def main():
    conn = await asyncpg.connect("postgresql://postgres:admin@localhost:5432/signalos")
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    print("TABLES:")
    for r in rows:
        print(f" - {r['table_name']}")
    await conn.close()
    
    print("\nSeeding initial data...")
    await seed_initial_data()
    print("Seed complete!")

if __name__ == "__main__":
    asyncio.run(main())
