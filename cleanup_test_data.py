#!/usr/bin/env python3
"""
Standalone cleanup script for Solar Hub API test data
Run this to clean up any leftover test data from failed test runs
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Clean up all test data"""
    print("🧹 Solar Hub API Test Data Cleanup")
    print("="*60)
    print("This script will remove ALL test data from your database:")
    print("• Test users (usernames starting with 'test_')")
    print("• Test hubs (countries starting with 'TestLand')")
    print("• Test batteries (with test secrets)")
    print("• Old live data (older than 1 hour)")
    print("")
    
    confirm = input("Do you want to proceed? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cleanup cancelled")
        return
    
    try:
        # Import database components
        print("📦 Importing database components...")
        try:
            from database import engine
            from models import User, SolarHub, BEPPPBattery, LiveData
            print("✅ Using root imports")
        except ImportError:
            try:
                from api.app.database import engine
                from api.app.models import User, SolarHub, BEPPPBattery, LiveData
                print("✅ Using api.app imports")
            except ImportError as e:
                print(f"❌ Failed to import database/models: {e}")
                return
        
        from sqlalchemy.orm import sessionmaker
        
        # Create session
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("\n🔍 Scanning for test data...")
        
        # Count existing test data
        test_users = db.query(User).filter(User.username.like('test_%')).count()
        test_hubs = db.query(SolarHub).filter(SolarHub.country.like('TestLand%')).count()
        test_batteries = db.query(BEPPPBattery).filter(
            BEPPPBattery.battery_secret.like('test-%')
        ).count()
        
        # Count old live data
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        old_live_data = db.query(LiveData).filter(
            LiveData.created_at < one_hour_ago
        ).count()
        
        print(f"Found:")
        print(f"  • {test_users} test users")
        print(f"  • {test_hubs} test hubs") 
        print(f"  • {test_batteries} test batteries")
        print(f"  • {old_live_data} old live data records")
        
        if test_users == 0 and test_hubs == 0 and test_batteries == 0 and old_live_data == 0:
            print("\n✅ No test data found - database is already clean!")
            db.close()
            return
        
        print(f"\n🔧 Cleaning up...")
        
        total_deleted = 0
        
        # Delete live data from test batteries first (foreign key constraint)
        for battery in db.query(BEPPPBattery).filter(BEPPPBattery.battery_secret.like('test-%')):
            deleted = db.query(LiveData).filter(LiveData.battery_id == battery.battery_id).delete()
            if deleted > 0:
                total_deleted += deleted
                print(f"✅ Deleted {deleted} live data records for battery {battery.battery_id}")
        
        # Delete old live data
        deleted_old = db.query(LiveData).filter(LiveData.created_at < one_hour_ago).delete()
        if deleted_old > 0:
            total_deleted += deleted_old
            print(f"✅ Deleted {deleted_old} old live data records")
        
        # Delete test batteries
        deleted_batteries = db.query(BEPPPBattery).filter(
            BEPPPBattery.battery_secret.like('test-%')
        ).delete(synchronize_session=False)
        if deleted_batteries > 0:
            total_deleted += deleted_batteries
            print(f"✅ Deleted {deleted_batteries} test batteries")
        
        # Delete test users
        deleted_users = db.query(User).filter(
            User.username.like('test_%')
        ).delete(synchronize_session=False)
        if deleted_users > 0:
            total_deleted += deleted_users
            print(f"✅ Deleted {deleted_users} test users")
        
        # Delete test hubs
        deleted_hubs = db.query(SolarHub).filter(
            SolarHub.country.like('TestLand%')
        ).delete(synchronize_session=False)
        if deleted_hubs > 0:
            total_deleted += deleted_hubs
            print(f"✅ Deleted {deleted_hubs} test hubs")
        
        # Clean up any other high-ID test records that might be leftover
        additional_batteries = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id > 10000).delete()
        additional_hubs = db.query(SolarHub).filter(SolarHub.hub_id > 10000).delete()
        
        if additional_batteries > 0 or additional_hubs > 0:
            total_deleted += additional_batteries + additional_hubs
            print(f"✅ Deleted {additional_batteries + additional_hubs} additional test records")
        
        # Commit all deletions
        db.commit()
        db.close()
        
        print(f"\n🎉 Cleanup complete!")
        print(f"Total records deleted: {total_deleted}")
        print("✨ Your database is now clean and ready for testing!")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        try:
            db.rollback()
            db.close()
        except:
            pass
        
        print("\nPlease check:")
        print("- Database connection")
        print("- Import paths")
        print("- Database permissions")

if __name__ == "__main__":
    main()