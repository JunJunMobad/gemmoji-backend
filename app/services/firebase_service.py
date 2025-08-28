from typing import List, Optional, Dict, Any
from google.cloud import firestore
from google.cloud.firestore import FieldFilter, Or, And

from ..firebase_config import get_firestore_client
from ..models import EmojiBase, Pack

class FirebaseService:
    
    def __init__(self):
        self.db = get_firestore_client()
    
    async def list_user_emojis(
        self, 
        query: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[int] = None,
        visibility: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if user_id:
                base_query = self.db.collection("emojis").document(user_id).collection("usersEmojis")
            else:
                base_query = self.db.collection_group("usersEmojis")
            
            if visibility:
                base_query = base_query.where("visibility", "==", visibility)
            
            if query:
                base_query = base_query.where("prompt", ">=", query).where("prompt", "<=", query + "\uf8ff")
            
            base_query = base_query.order_by("createdAt", direction=firestore.Query.DESCENDING)
            
            base_query = base_query.limit(limit)
            
            if cursor:
                base_query = base_query.start_after({"createdAt": cursor})
            
            results = base_query.stream()
            emojis = []
            
            for doc in results:
                doc_data = doc.to_dict()
                if 'createdAt' in doc_data and hasattr(doc_data['createdAt'], 'timestamp'):
                    doc_data['createdAt'] = int(doc_data['createdAt'].timestamp() * 1000)
                emojis.append(EmojiBase(**doc_data))
            
            next_cursor = emojis[-1].createdAt if len(emojis) == limit else None
            has_more = len(emojis) == limit
            
            return {
                "emojis": emojis,
                "next_cursor": next_cursor,
                "has_more": has_more
            }
            
        except Exception as e:
            print(f"Error in list_user_emojis: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    async def list_user_packs(
        self, 
        query: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[int] = None,  
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if user_id:
                base_query = self.db.collection("packs").document(user_id).collection("userPacks")
            else:
                base_query = self.db.collection_group("userPacks")
            
            if query:
                base_query = base_query.where(
                    filter=Or([
                        And([
                            FieldFilter("name", ">=", query),
                            FieldFilter("name", "<=", query + "\uf8ff")
                        ]),
                        And([
                            FieldFilter("description", ">=", query),
                            FieldFilter("description", "<=", query + "\uf8ff")
                        ])
                    ])
                )
            
            base_query = base_query.order_by("createdAt", direction=firestore.Query.DESCENDING)
            
            base_query = base_query.limit(limit)
            
            if cursor:
                base_query = base_query.start_after({"createdAt": cursor})
            
            results = base_query.stream()
            packs = []
            
            for doc in results:
                doc_data = doc.to_dict()
                if 'createdAt' in doc_data and hasattr(doc_data['createdAt'], 'timestamp'):
                    doc_data['createdAt'] = int(doc_data['createdAt'].timestamp() * 1000)
                packs.append(Pack(**doc_data))
            
            next_cursor = packs[-1].createdAt if len(packs) == limit else None
            has_more = len(packs) == limit
            
            return {
                "packs": packs,
                "next_cursor": next_cursor,
                "has_more": has_more
            }
            
        except Exception as e:
            print(f"Error in list_user_packs: {str(e)}")
            import traceback
            traceback.print_exc()
            raise