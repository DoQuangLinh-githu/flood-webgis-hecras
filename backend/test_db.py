# backend/test_db.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

print("=" * 60)
print("TESTING DATABASE CONNECTION")
print("=" * 60)
print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Not found'}")

try:
    # Tạo engine
    engine = create_engine(DATABASE_URL)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        print(f"✅ Query result: {result.scalar()}")
        
        # Kiểm tra bảng
        tables = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        print("\n📋 Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
            
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    import traceback
    traceback.print_exc()