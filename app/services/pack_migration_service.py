from typing import List
from datetime import datetime
from google.cloud import firestore

from ..firebase_config import get_firestore_client
from ..models import Pack, PackMigrationData

class PackMigrationService:
    
    def __init__(self):
        self.db = get_firestore_client()
    
    async def migrate_pack_to_firestore(self, pack_data: PackMigrationData, user_id: str) -> str:
        try:
            created_at_dt = datetime.fromisoformat(pack_data.created_at)
            scraped_at_dt = datetime.fromisoformat(pack_data.scraped_at)
            created_at_ms = int(created_at_dt.timestamp() * 1000)
            scraped_at_ms = int(scraped_at_dt.timestamp() * 1000)
            
            pack = Pack(
                name=pack_data.name,
                url=pack_data.url,
                downloadCount=pack_data.download_count,
                emojiCount=pack_data.emoji_count,
                description=pack_data.description,
                createdAt=created_at_ms,
                scrapedAt=scraped_at_ms,
                userID=user_id
            )
            
            doc_ref = self.db.collection("packs").document(user_id).collection("userPacks").document()
            doc_ref.set(pack.dict())
            
            print(f"✅ Migrated pack '{pack_data.name}' with ID: {doc_ref.id}")
            print(f"   📊 Fields: createdAt={created_at_ms}, downloadCount={pack_data.download_count}, emojiCount={pack_data.emoji_count}")
            return doc_ref.id
            
        except Exception as e:
            print(f"❌ Error migrating pack '{pack_data.name}': {str(e)}")
            raise
    
    async def migrate_packs_from_json(self, packs_data: List[PackMigrationData], user_id: str) -> List[str]:    
        migrated_ids = []
        
        print(f"🚀 Starting migration of {len(packs_data)} packs for user {user_id}")
        
        for i, pack_data in enumerate(packs_data, 1):
            try:
                doc_id = await self.migrate_pack_to_firestore(pack_data, user_id)
                migrated_ids.append(doc_id)
                print(f"✅ Progress: {i}/{len(packs_data)} packs migrated")
                
            except Exception as e:
                print(f"❌ Failed to migrate pack {i}/{len(packs_data)}: {str(e)}")
                continue
        
        print(f"🎉 Migration completed! Successfully migrated {len(migrated_ids)}/{len(packs_data)} packs")
        return migrated_ids