from app.db.database import SessionLocal
from app.models.disaster_type_model import DisasterType
from app.models.needs_model import Needs
from app.models.region_model import Region
from app.models.rescue_request_model import RescueRequest
from sqlalchemy import func


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def seed():
    db = SessionLocal()
    try:
        print("🌱 Seeding database...")
        
        # Disaster Types
        dt_flood = get_or_create(db, DisasterType, name='Lũ lụt', description='Thiên tai lũ lụt')
        dt_fire = get_or_create(db, DisasterType, name='Hỏa hoạn', description='Hỏa hoạn, cháy nổ')
        dt_storm = get_or_create(db, DisasterType, name='Bão', description='Bão và gió mạnh')
        dt_earthquake = get_or_create(db, DisasterType, name='Động đất', description='Động đất')
        print(f"✓ Created {db.query(DisasterType).count()} disaster types")

        # Needs
        need_food = get_or_create(db, Needs, name='Lương thực', description='Nhu cầu lương thực, thực phẩm')
        need_water = get_or_create(db, Needs, name='Nước sạch', description='Nhu cầu nước uống sạch')
        need_medicine = get_or_create(db, Needs, name='Thuốc men', description='Thuốc men, vật tư y tế')
        need_shelter = get_or_create(db, Needs, name='Nơi ở', description='Nơi trú ẩn tạm thời')
        need_rescue = get_or_create(db, Needs, name='Cứu hộ', description='Cần cứu hộ khẩn cấp')
        print(f"✓ Created {db.query(Needs).count()} needs")

        # Regions
        reg_hanoi = get_or_create(db, Region, name='Hà Nội')
        reg_hcm = get_or_create(db, Region, name='Hồ Chí Minh')
        reg_danang = get_or_create(db, Region, name='Đà Nẵng')
        reg_haiphong = get_or_create(db, Region, name='Hải Phòng')
        print(f"✓ Created {db.query(Region).count()} regions")

        # Sample rescue requests with different locations
        sample_rescues = [
            {
                'title': 'Cần hỗ trợ khẩn cấp - Lũ lụt Hà Nội',
                'content': 'Khu vực Hoàng Mai bị ngập nặng, cần cứu hộ khẩn cấp. Nhiều hộ dân bị cô lập.',
                'location': 'Hoàng Mai, Hà Nội',
                'coordinate': (105.840776, 20.971258),  # lng, lat
                'region': reg_hanoi,
                'urgency_score': 3.0,
                'reliability_score': 2.5,
                'contact': '0912345678',
                'affected_people': 50,
                'is_isolated': True,
                'infrastructure_damage': True,
            },
            {
                'title': 'Cần nước sạch và lương thực',
                'content': 'Sau bão, khu vực Sơn Trà cần hỗ trợ nước sạch và lương thực',
                'location': 'Sơn Trà, Đà Nẵng',
                'coordinate': (108.2397, 16.0902),
                'region': reg_danang,
                'urgency_score': 2.0,
                'reliability_score': 3.0,
                'contact': '0987654321',
                'affected_people': 30,
                'infrastructure_damage': False,
            },
            {
                'title': 'Hỏa hoạn cần hỗ trợ y tế',
                'content': 'Vụ cháy tại quận 1, có người bị thương cần hỗ trợ y tế',
                'location': 'Quận 1, TP Hồ Chí Minh',
                'coordinate': (106.6977, 10.7717),
                'region': reg_hcm,
                'urgency_score': 3.0,
                'reliability_score': 3.0,
                'contact': '0901234567',
                'affected_people': 5,
                'has_emergency': True,
            },
        ]

        for rescue_data in sample_rescues:
            # Check if already exists
            existing = db.query(RescueRequest).filter(
                RescueRequest.title == rescue_data['title']
            ).first()
            
            if not existing:
                coord = rescue_data.pop('coordinate', None)
                coordinate_geom = None
                if coord:
                    lng, lat = coord
                    coordinate_geom = func.ST_GeomFromText(f'POINT({lng} {lat})', 4326)
                
                rr = RescueRequest(
                    title=rescue_data['title'],
                    content=rescue_data['content'],
                    location=rescue_data['location'],
                    coordinate=coordinate_geom,
                    region_id=rescue_data['region'].id,
                    urgency_score=rescue_data.get('urgency_score', 2.0),
                    reliability_score=rescue_data.get('reliability_score', 2.0),
                    contact=rescue_data.get('contact'),
                    affected_people=rescue_data.get('affected_people', 0),
                    is_isolated=rescue_data.get('is_isolated', False),
                    infrastructure_damage=rescue_data.get('infrastructure_damage', False),
                    has_emergency=rescue_data.get('has_emergency', False),
                )
                db.add(rr)
                db.commit()
                db.refresh(rr)
                print(f'✓ Inserted: {rr.title} (id={rr.id})')
            else:
                print(f'⊘ Already exists: {existing.title} (id={existing.id})')

        print('\n✅ Seed completed!')

    except Exception as e:
        print(f'❌ Error: {str(e)}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()