import os
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# Convert postgres:// to postgresql+asyncpg:// for async compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Create engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
metadata = MetaData()
Base = declarative_base(metadata=metadata)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class Database:
    def __init__(self):
        self.engine = engine
        
    async def connect(self):
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("Database connected successfully")
        except Exception as e:
            print(f"Database connection error: {e}")
        
    async def disconnect(self):
        await self.engine.dispose()
        
    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

database = Database()
