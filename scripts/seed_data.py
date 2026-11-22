"""
Seed initial data for disaster_type and needs tables
"""
from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
from app.models.disaster_type_model import DisasterType
from app.models.needs_model import Needs

def seed_disaster_types():
    """Seed disaster types"""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(DisasterType).first()
        if existing:
            print("⚠ Disaster types already seeded. Skipping...")
            return
        
        disaster_types = [
            {"name": "Lũ lụt", "description": "Lũ lụt, ngập lụt do mưa bão"},
            {"name": "Ngập nước", "description": "Ngập nước cục bộ"},
            {"name": "Không xác định", "description": "Loại thiên tai chưa xác định"},
        ]
        
        for dt in disaster_types:
            item = DisasterType(**dt)
            db.add(item)
        
        db.commit()
        print(f"✓ Đã seed {len(disaster_types)} disaster types")
    except Exception as e:
        print(f"✗ Lỗi khi seed disaster types: {e}")
        db.rollback()
    finally:
        db.close()

def seed_needs():
    """Seed needs"""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(Needs).first()
        if existing:
            print("⚠ Needs already seeded. Skipping...")
            return
        
        needs_list = [
            {"name": "Lương thực & nước uống", "description": "Thức ăn, nước uống sạch"},
            {"name": "Thuốc men & hỗ trợ y tế", "description": "Thuốc men, dụng cụ y tế, nhân viên y tế"},
            {"name": "Chỗ ở & nơi trú ẩn", "description": "Nơi ở tạm thời, chỗ trú ẩn an toàn"},
            {"name": "Phương tiện & cứu hộ", "description": "Phương tiện di chuyển, thiết bị cứu hộ"},
            {"name": "Liên lạc & thông tin", "description": "Phương tiện liên lạc, thông tin về tình hình"},
            {"name": "Vật dụng sinh hoạt (áo phao, đèn pin, quần áo, mền chăn)", "description": "Đồ dùng sinh hoạt thiết yếu"},
        ]
        
        for need in needs_list:
            item = Needs(**need)
            db.add(item)
        
        db.commit()
        print(f"✓ Đã seed {len(needs_list)} needs")
    except Exception as e:
        print(f"✗ Lỗi khi seed needs: {e}")
        db.rollback()
    finally:
        db.close()

def seed_all():
    """Seed all initial data"""
    print("Starting seed data...")
    seed_disaster_types()
    seed_needs()
    print("✅ Seed completed!")

if __name__ == "__main__":
    seed_all()
