from typing import List, Optional, Dict, Any
from google.cloud import firestore
from google.cloud.firestore import FieldFilter, Or, And

from ..firebase_config import get_firestore_client
from ..models import EmojiBase, Pack
from .gemini_service import GeminiService

class FirebaseService:
    
    def __init__(self):
        self.db = get_firestore_client()
        self.gemini_service = GeminiService()
    
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
    
    async def increment_emoji_download_count(self, user_id: str, emoji_id: str) -> Dict[str, Any]:
        try:
            doc_ref = self.db.collection("emojis").document(user_id).collection("usersEmojis").document(emoji_id)
            
            doc_ref.update({
                "downloadCount": firestore.Increment(1)
            })
            
            updated_doc = doc_ref.get()
            if not updated_doc.exists:
                raise ValueError(f"Emoji not found: {emoji_id}")
            
            doc_data = updated_doc.to_dict()
            current_count = doc_data.get('downloadCount', 0)
            
            return {
                "success": True,
                "emojiID": emoji_id,
                "downloadCount": current_count,
                "message": f"Download count incremented to {current_count}"
            }
            
        except Exception as e:
            print(f"Error incrementing download count: {str(e)}")
            raise
    
    async def categorize_emoji(self, user_id: str, emoji_id: str) -> Dict[str, Any]:
        """Categorize an emoji using Gemini AI and update Firestore"""
        try:
            doc_ref = self.db.collection("emojis").document(user_id).collection("usersEmojis").document(emoji_id)
            
            doc = doc_ref.get()
            if not doc.exists:
                raise ValueError(f"Emoji not found: {emoji_id}")
            
            doc_data = doc.to_dict()
            prompt = doc_data.get('prompt')
            if not prompt:
                raise ValueError(f"No prompt found for emoji: {emoji_id}")
            
            category = await self.gemini_service.categorize_emoji_prompt(prompt)
            
            doc_ref.update({
                "category": category
            })
            
            return {
                "success": True,
                "emojiID": emoji_id,
                "prompt": prompt,
                "category": category,
                "message": f"Emoji categorized as '{category}'"
            }
            
        except Exception as e:
            print(f"Error categorizing emoji: {str(e)}")
            raise
    
    async def update_emoji_visibility(self, user_id: str, emoji_id: str, visibility: str) -> Dict[str, Any]:
        """Update emoji visibility (Public/Private)"""
        try:
            if visibility not in ["Public", "Private"]:
                raise ValueError("Visibility must be 'Public' or 'Private'")
            
            doc_ref = self.db.collection("emojis").document(user_id).collection("usersEmojis").document(emoji_id)
            
            doc = doc_ref.get()
            if not doc.exists:
                raise ValueError(f"Emoji not found: {emoji_id}")
            
            doc_ref.update({
                "visibility": visibility
            })
            
            return {
                "success": True,
                "emojiID": emoji_id,
                "visibility": visibility,
                "message": f"Emoji visibility updated to {visibility}"
            }
            
        except Exception as e:
            print(f"Error updating emoji visibility: {str(e)}")
            raise