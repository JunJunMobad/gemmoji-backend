from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

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
    user_id: Optional[str] = Query(None, description="Filter by specific user ID. If not provided, fetches emojis from all users"),
    category: Optional[str] = Query(None, description="Filter by category (Animals, Celebrities, Memes, Food, Emotions)")
):
    """List emojis by category, ordered by creation date"""
    try:
        result = await firebase_service.list_user_emojis(
            query=query,
            limit=limit,
            cursor=cursor,
            visibility=visibility,
            user_id=user_id,
            category=category
        )
        return EmojiListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list emojis: {str(e)}")

class DownloadResponse(BaseModel):
    success: bool
    emojiID: str
    downloadCount: int
    message: str

class CategorizeResponse(BaseModel):
    success: bool
    emojiID: str
    prompt: str
    category: str
    message: str

class VisibilityUpdateRequest(BaseModel):
    user_id: str
    emoji_id: str
    visibility: str

class VisibilityResponse(BaseModel):
    success: bool
    emojiID: str
    visibility: str
    message: str

@router.post("/{user_id}/{emoji_id}/download", response_model=DownloadResponse)
async def increment_download_count(
    user_id: str = Path(..., description="User ID who owns the emoji"),
    emoji_id: str = Path(..., description="Emoji ID to increment download count for")
):
    """Increment download count for an emoji"""
    try:
        result = await firebase_service.increment_emoji_download_count(user_id, emoji_id)
        return DownloadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to increment download count: {str(e)}")

@router.post("/{user_id}/{emoji_id}/categorize", response_model=CategorizeResponse)
async def categorize_emoji(
    user_id: str = Path(..., description="User ID who owns the emoji"),
    emoji_id: str = Path(..., description="Emoji ID to categorize")
):
    """Categorize an emoji using AI"""
    try:
        result = await firebase_service.categorize_emoji(user_id, emoji_id)
        return CategorizeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to categorize emoji: {str(e)}")

@router.put("/visibility", response_model=VisibilityResponse)
async def update_emoji_visibility(request: VisibilityUpdateRequest):
    """Update emoji visibility between Public and Private"""
    try:
        result = await firebase_service.update_emoji_visibility(
            request.user_id, 
            request.emoji_id, 
            request.visibility
        )
        return VisibilityResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update visibility: {str(e)}")

@router.get("/popular", response_model=EmojiListResponse)
async def list_popular_emojis(
    query: Optional[str] = Query(None, description="Text to search in the prompt field"),
    limit: int = Query(20, ge=1, le=100, description="Number of records per page"),
    cursor: Optional[int] = Query(None, description="Cursor for pagination (createdAt timestamp)"),
    visibility: Optional[str] = Query(None, description="Filter by visibility (Public/Private)"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID. If not provided, fetches emojis from all users")
):
    """List emojis by popularity (downloadCount), ordered by download count and creation date"""
    try:
        result = await firebase_service.list_popular_emojis(
            query=query,
            limit=limit,
            cursor=cursor,
            visibility=visibility,
            user_id=user_id
        )
        return EmojiListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list popular emojis: {str(e)}")