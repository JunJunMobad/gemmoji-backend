from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..services.firebase_service import FirebaseService
from ..models import EmojiListResponse

router = APIRouter()
firebase_service = FirebaseService()

@router.get("/", response_model=EmojiListResponse)
async def list_emojis(
    query: Optional[str] = Query(None, description="Text to search in the prompt field"),
    limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
    cursor: Optional[int] = Query(None, description="Cursor for pagination (createdAt timestamp)"),
    visibility: Optional[str] = Query(None, description="Filter by visibility (Public/Private)"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID. If not provided, fetches emojis from all users")
):
    """
    List emojis with efficient cursor-based pagination
    
    - **query**: Optional text to search in the prompt field (partial match)
    - **limit**: Number of records per page (default: 20, max: 100)
    - **cursor**: Cursor for pagination (createdAt timestamp from previous response)
    - **visibility**: Filter by visibility (Public/Private)
    - **user_id**: Optional user ID to filter emojis. If not provided, fetches emojis from all users
    
    Returns emojis with next_cursor for efficient pagination. Use next_cursor as cursor parameter for the next page.
    """
    try:
        result = await firebase_service.list_user_emojis(
            query=query,
            limit=limit,
            cursor=cursor,
            visibility=visibility,
            user_id=user_id
        )
        return EmojiListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list emojis: {str(e)}")