import asyncio
import time
import sys
import traceback
from dotenv import load_dotenv
import os

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath("."))

load_dotenv(".env")
url = os.environ.get("DATABASE_URL", "")

# Mask password
masked_url = url
if "@" in url and ":" in url:
    parts = url.split("@")
    first_part = parts[0]
    if ":" in first_part.replace("postgresql+asyncpg://", ""):
        parts2 = first_part.split(":")
        masked_url = ":".join(parts2[:-1]) + ":***@" + parts[1]
        
print(f"Testing URL: {masked_url}")

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run_tests():
    try:
        print("1. Raw asyncpg connection test...")
        start = time.time()
        # asyncpg needs postgresql:// not postgresql+asyncpg://
        asyncpg_url = url.replace("postgresql+asyncpg", "postgresql")
        conn = await asyncpg.connect(asyncpg_url)
        latency = (time.time() - start) * 1000
        print(f"   Success. Latency: {latency:.2f}ms")

        print("3. Test SELECT 1...")
        val = await conn.fetchval('SELECT 1')
        print(f"   Success. Returned: {val}")

        print("4. Test CREATE EXTENSION IF NOT EXISTS vector...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("   Success.")
        await conn.close()
    except Exception as e:
        print(f"   FAIL: {e}")
        traceback.print_exc()
        return

    try:
        print("2. SQLAlchemy engine creation test...")
        engine = create_async_engine(url, echo=False)
        print("   Success.")
        
        from backend.db.database import init_db
        print("5. Test init_db()...")
        await init_db()
        print("   Success.")
        
    except Exception as e:
        print(f"   FAIL: {e}")
        traceback.print_exc()
        return
        
    try:
        print("6. Attempt FastAPI startup...")
        from backend.main import app
        # Since uvicorn runs its own event loop, we just verify import and routes
        print(f"   FastAPI app loaded. Title: {app.title}, Routes: {len(app.routes)}")
    except Exception as e:
        print(f"   FAIL: {e}")
        traceback.print_exc()
        return

asyncio.run(run_tests())
