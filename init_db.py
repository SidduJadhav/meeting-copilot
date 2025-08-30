# simple_init.py
import asyncio
import asyncpg

async def init_simple_db():
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            'postgresql://meeting:1234@localhost:5432/meeting'
        )
        
        # Enable UUID extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        
        # Create your tables here (simplified)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("✅ Simple database setup completed!")
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(init_simple_db())