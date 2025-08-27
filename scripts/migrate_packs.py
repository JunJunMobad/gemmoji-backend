import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from app.firebase_config import initialize_firebase
from app.services.pack_migration_service import PackMigrationService
from app.models import PackMigrationData

USER_ID = "gs8uhH0QtpfHDQgTa2YXf2Zdb9K2"

JSON_FILE_PATH = project_root / "scripts" / "data" / "packs_test.json"

async def load_pack_data() -> list[PackMigrationData]:
    if not JSON_FILE_PATH.exists():
        raise FileNotFoundError(f"JSON file not found: {JSON_FILE_PATH}")
    
    print(f"📂 Loading pack data from: {JSON_FILE_PATH}")
    
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
        raw_data = json.load(file)
    
    pack_data = []
    for item in raw_data:
        try:
            pack = PackMigrationData(**item)
            pack_data.append(pack)
        except Exception as e:
            print(f"❌ Invalid pack data: {item.get('name', 'Unknown')} - {str(e)}")
            continue
    
    print(f"✅ Loaded {len(pack_data)} valid packs from {len(raw_data)} total items")
    return pack_data

async def main():
    try:
        print("🚀 Starting Pack Migration to Firestore")
        print("=" * 50)
        
        print("🔧 Initializing Firebase...")
        initialize_firebase()
        print("✅ Firebase initialized successfully")
        
        pack_data = await load_pack_data()
        
        if not pack_data:
            print("❌ No valid pack data found. Exiting.")
            return
        
        migration_service = PackMigrationService()
        
        print(f"\n📋 Migration Summary:")
        print(f"   • Source file: {JSON_FILE_PATH}")
        print(f"   • Target user ID: {USER_ID}")
        print(f"   • Number of packs: {len(pack_data)}")
        print(f"   • Firestore structure: packs/{USER_ID}/userPacks/{{auto_id}}")
        
        response = input("\n🤔 Do you want to proceed with the migration? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Migration cancelled by user")
            return
        
        print("\n🚀 Starting migration...")
        migrated_ids = await migration_service.migrate_packs_from_json(pack_data, USER_ID)
        
        print("\n" + "=" * 50)
        print("📊 Migration Summary:")
        print(f"   • Total packs processed: {len(pack_data)}")
        print(f"   • Successfully migrated: {len(migrated_ids)}")
        print(f"   • Failed: {len(pack_data) - len(migrated_ids)}")
        
        if migrated_ids:
            print(f"\n✅ Migration completed successfully!")
            print(f"   Packs are now available in Firestore at: packs/{USER_ID}/userPacks/")
        else:
            print("\n❌ Migration failed - no packs were migrated")
            
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if not os.getenv("FIREBASE_CREDENTIALS_JSON") and not os.getenv("FIREBASE_CREDENTIALS_PATH"):
        print("❌ Error: Firebase credentials not configured")
        print("   Please set either:")
        print("   1. FIREBASE_CREDENTIALS_JSON environment variable with the full JSON content, or")
        print("   2. FIREBASE_CREDENTIALS_PATH environment variable pointing to your serviceAccountKey.json file")
        sys.exit(1)
    
    asyncio.run(main())