#!/usr/bin/env python3
"""
Add downloadCount Field to Emojis

This script adds the downloadCount field with value 0 to all existing emojis
that don't already have this field.

Usage:
    python scripts/add_download_count.py

Environment variables required:
    FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv()

from app.firebase_config import initialize_firebase, get_firestore_client

async def add_download_count_with_batching(db):
    """Add downloadCount using collection group query with batching"""
    try:
        print("🔄 Using collection group query with small batches...")
        
        # Track statistics
        total_updated = 0
        total_already_has_field = 0
        total_error_count = 0
        batch_size = 100
        
        # Use collection group query with small batches
        emojis_ref = db.collection_group("usersEmojis")
        
        # Process in small batches
        last_doc = None
        batch_num = 1
        
        while True:
            print(f"   Processing batch {batch_num}...")
            
            # Build query for this batch
            query = emojis_ref.limit(batch_size)
            if last_doc:
                query = query.start_after(last_doc)
            
            # Get batch of documents
            batch_docs = list(query.stream())
            
            if not batch_docs:
                print("   No more documents to process")
                break
            
            # Process this batch
            batch_updated = 0
            batch_skipped = 0
            batch_errors = 0
            
            for emoji_doc in batch_docs:
                try:
                    emoji_data = emoji_doc.to_dict()
                    
                    # Check if downloadCount field already exists
                    if 'downloadCount' in emoji_data:
                        batch_skipped += 1
                        continue
                    
                    # Add downloadCount field with value 0
                    emoji_doc.reference.update({
                        "downloadCount": 0
                    })
                    batch_updated += 1
                    
                except Exception as e:
                    batch_errors += 1
                    print(f"     ❌ Error updating emoji {emoji_doc.id}: {str(e)}")
                    continue
            
            # Update totals
            total_updated += batch_updated
            total_already_has_field += batch_skipped
            total_error_count += batch_errors
            
            print(f"     ✅ Batch {batch_num}: Updated {batch_updated}, Skipped {batch_skipped}, Errors {batch_errors}")
            
            # Set up for next batch
            last_doc = batch_docs[-1]
            batch_num += 1
            
            # Break if we got fewer docs than batch_size (last batch)
            if len(batch_docs) < batch_size:
                break
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 Migration Summary:")
        print(f"   • Total batches processed: {batch_num - 1}")
        print(f"   • Successfully updated emojis: {total_updated}")
        print(f"   • Already had downloadCount: {total_already_has_field}")
        print(f"   • Errors: {total_error_count}")
        
        if total_updated > 0:
            print(f"\n✅ Successfully added downloadCount field to {total_updated} emojis!")
        else:
            print(f"\n✅ All emojis already have downloadCount field!")
            
        return True
        
    except Exception as e:
        print(f"❌ Batching migration failed: {str(e)}")
        return False

async def process_user_emojis(db, user_id, updated_count, already_has_field, error_count):
    """Process emojis for a specific user"""
    try:
        print(f"   Processing user: {user_id}")
        user_emojis_ref = db.collection("emojis").document(user_id).collection("usersEmojis")
        user_emojis = list(user_emojis_ref.stream())
        
        user_updated = 0
        user_skipped = 0
        user_errors = 0
        
        for emoji_doc in user_emojis:
            try:
                emoji_data = emoji_doc.to_dict()
                
                # Check if downloadCount field already exists
                if 'downloadCount' in emoji_data:
                    user_skipped += 1
                    continue
                
                # Add downloadCount field with value 0
                emoji_doc.reference.update({
                    "downloadCount": 0
                })
                user_updated += 1
                
            except Exception as e:
                user_errors += 1
                print(f"     ❌ Error updating emoji {emoji_doc.id}: {str(e)}")
                continue
        
        print(f"     ✅ User {user_id}: Updated {user_updated}, Skipped {user_skipped}, Errors {user_errors}")
        return user_updated, user_skipped, user_errors
        
    except Exception as e:
        print(f"     ❌ Error processing user {user_id}: {str(e)}")
        return 0, 0, 1

async def add_download_count_to_emojis():
    """Add downloadCount field to all emojis that don't have it"""
    try:
        print("🚀 Starting downloadCount field addition")
        print("=" * 50)
        
        # Initialize Firebase
        print("🔧 Initializing Firebase...")
        initialize_firebase()
        db = get_firestore_client()
        print("✅ Firebase initialized successfully")
        
        # Get all users first (to avoid collection group timeout)
        print("\n📊 Getting all users...")
        users_ref = db.collection("emojis")
        all_users = list(users_ref.stream())
        
        print(f"📋 Found {len(all_users)} users with emojis")
        
        # If no users found, let's check if we need to use collection group query with smaller batches
        if len(all_users) == 0:
            print("⚠️  No users found in emojis collection. Trying collection group query with batching...")
            return await add_download_count_with_batching(db)
        
        # Track statistics
        total_updated = 0
        total_already_has_field = 0
        total_error_count = 0
        
        print("\n🔄 Processing users...")
        
        for i, user_doc in enumerate(all_users, 1):
            user_id = user_doc.id
            
            try:
                updated, skipped, errors = await process_user_emojis(
                    db, user_id, total_updated, total_already_has_field, total_error_count
                )
                
                total_updated += updated
                total_already_has_field += skipped
                total_error_count += errors
                
                # Progress update
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(all_users)} users processed")
                
            except Exception as e:
                total_error_count += 1
                print(f"❌ Error processing user {user_id}: {str(e)}")
                continue
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 Migration Summary:")
        print(f"   • Total users processed: {len(all_users)}")
        print(f"   • Successfully updated emojis: {total_updated}")
        print(f"   • Already had downloadCount: {total_already_has_field}")
        print(f"   • Errors: {total_error_count}")
        
        if total_updated > 0:
            print(f"\n✅ Successfully added downloadCount field to {total_updated} emojis!")
        else:
            print(f"\n✅ All emojis already have downloadCount field!")
            
    except KeyboardInterrupt:
        print("\n❌ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def main():
    """Main function"""
    print("🎯 Add downloadCount Field to Emojis")
    print("This will add downloadCount=0 to all emojis that don't have this field")
    
    # Confirm operation
    response = input("\n🤔 Do you want to proceed? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Operation cancelled by user")
        return
    
    await add_download_count_to_emojis()

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("FIREBASE_CREDENTIALS_JSON") and not os.getenv("FIREBASE_CREDENTIALS_PATH"):
        print("❌ Error: Firebase credentials not configured")
        print("   Please set either:")
        print("   1. FIREBASE_CREDENTIALS_JSON environment variable with the full JSON content, or")
        print("   2. FIREBASE_CREDENTIALS_PATH environment variable pointing to your serviceAccountKey.json file")
        sys.exit(1)
    
    # Run the migration
    asyncio.run(main())