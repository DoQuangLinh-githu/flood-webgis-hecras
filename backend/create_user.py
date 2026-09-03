# backend/create_user.py

import os
import sys
from pathlib import Path

# Thêm backend vào path
sys.path.insert(0, str(Path(__file__).parent))

# Import tất cả models trước khi tạo user
from app.models import User, SimulationJob, SimulationParameter, SimulationResult, Agent, AuditLog
from app.core.database import SessionLocal
from app.core.config import settings

def create_system_user():
    print("=" * 60)
    print("CREATING SYSTEM USER")
    print("=" * 60)
    
    db_url = settings.DATABASE_URL
    if '@' in db_url:
        db_info = db_url.split('@')[1].split('?')[0]
        print(f"Database: {db_info}")
    else:
        print("Database: Neon PostgreSQL")
    
    db = SessionLocal()
    try:
        # Kiểm tra user đã tồn tại chưa
        user = db.query(User).filter(User.email == 'system@example.com').first()
        if not user:
            user = User(
                email='system@example.com',
                username='system',
                password_hash='system_hash',
                role='admin'
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("\n✅ System user created successfully!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
        else:
            print("\n✅ System user already exists!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
        
        # Hiển thị danh sách users
        users = db.query(User).all()
        print(f"\n📋 Users in database ({len(users)}):")
        for u in users:
            print(f"  - {u.email} ({u.role})")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)

if __name__ == "__main__":
    create_system_user()