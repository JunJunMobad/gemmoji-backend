"""
Pack API routes
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..services.firebase_service import FirebaseService
from ..models import PackListResponse

router = APIRouter()
firebase_service = FirebaseService()

@router.get("/", response_model=PackListResponse)
async def list_packs(
    query: Optional[str] = Query(None, description="Text to search in the pack name and description fields (prefix match)"),
    limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
    cursor: Optional[int] = Query(None, description="Cursor for pagination (createdAt timestamp)"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID. If not provided, fetches packs from all users")
):
    """
    List packs with efficient cursor-based pagination
    
    - **query**: Optional text to search in the pack name and description fields (prefix match)
    - **limit**: Number of records per page (default: 20, max: 100)
    - **cursor**: Cursor for pagination (createdAt timestamp from previous response)
    - **user_id**: Optional user ID to filter packs. If not provided, fetches packs from all users
    
    Returns packs with next_cursor for efficient pagination. Use next_cursor as cursor parameter for the next page.
    """
    try:
        result = await firebase_service.list_user_packs(
            query=query,
            limit=limit,
            cursor=cursor,
            user_id=user_id
        )
        return PackListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list packs: {str(e)}")