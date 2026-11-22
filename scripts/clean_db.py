"""
Script to delete all data from database
WARNING: This will DELETE ALL DATA in all tables!
"""
from sqlalchemy import text
from app.db.database import engine, Base

def drop_all_tables():
    """Drop all tables in the database"""
    print("⚠️  WARNING: This will DELETE ALL TABLES and DATA!")
    confirm = input("Type 'DELETE ALL' to confirm: ")
    
    if confirm != "DELETE ALL":
        print("❌ Aborted. No changes made.")
        return
    
    print("\n🗑️  Dropping all tables...")
    
    try:
        # Drop all tables defined in models
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully!")
        
        # Optionally recreate tables (empty)
        recreate = input("\nDo you want to recreate empty tables? (y/n): ")
        if recreate.lower() == 'y':
            Base.metadata.create_all(bind=engine)
            print("✅ Empty tables recreated!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def truncate_all_tables():
    """Delete all data but keep table structure"""
    print("⚠️  WARNING: This will DELETE ALL DATA but keep table structure!")
    confirm = input("Type 'TRUNCATE ALL' to confirm: ")
    
    if confirm != "TRUNCATE ALL":
        print("❌ Aborted. No changes made.")
        return
    
    print("\n🗑️  Truncating all tables...")
    
    try:
        with engine.connect() as conn:
            # Disable foreign key checks temporarily
            conn.execute(text("SET session_replication_role = 'replica';"))
            
            # Get all table names
            tables = [
                'rescue_request_needs',
                'rescue_request_disaster_types',
                'rescue_request',
                'needs',
                'disaster_type',
                'region',
            ]
            
            for table in tables:
                try:
                    conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                    print(f"✓ Truncated {table} and reset ID")
                except Exception as e:
                    print(f"⚠ {table}: {e}")
            
            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = 'origin';"))
            conn.commit()
            
        print("\n✅ All data deleted successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Database Cleanup Tool ===\n")
    print("1. Drop all tables (delete structure + data)")
    print("2. Truncate all tables (keep structure, delete data)")
    print("3. Cancel")
    
    choice = input("\nSelect option (1/2/3): ")
    
    if choice == "1":
        drop_all_tables()
    elif choice == "2":
        truncate_all_tables()
    else:
        print("❌ Cancelled.")
