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
    query: Optional[str] = Query(
        None, description="Text to search in the pack name and description fields"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
    cursor: Optional[int] = Query(
        None, description="Page offset - order number of first pack for next page"
    ),
    user_id: Optional[str] = Query(
        None,
        description="Filter by specific user ID. If not provided, fetches packs from all users",
    ),
):
    """List packs by recent (newest first)"""
    try:
        result = await firebase_service.list_packs(
            query=query, limit=limit, cursor=cursor, user_id=user_id
        )
        return PackListResponse(**result)
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"Error in list_packs: {str(e)}")
        print(f"Request params: limit={limit}, cursor={cursor}")
        print(f"Full traceback:\n{error_details}")

        error_msg = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(
            status_code=500, detail=f"Failed to list packs: {error_msg}"
        )
