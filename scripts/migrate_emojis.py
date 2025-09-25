#!/usr/bin/env python3
"""
Migrate Emojis to Firestore

This script migrates all emojis from scripts/data/emojis.json to Firestore
with proper categorization using AI and specified field mappings.

Usage:
    python scripts/migrate_emojis.py

Environment variables required:
    FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON
    GEMINI_API_KEY
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from app.firebase_config import initialize_firebase, get_firestore_client
from app.services.gemini_service import GeminiService

FIXED_USER_ID = "gs8uhH0QtpfHDQgTa2YXf2Zdb9K2"
DEFAULT_DOWNLOAD_COUNT = 10
DEFAULT_VISIBILITY = "Public"


class EmojiMigrationService:
    """Service to handle emoji migration from JSON to Firestore"""

    def __init__(self):
        self.db = get_firestore_client()
        self.gemini_service = GeminiService()

    def load_emojis_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Load emojis from JSON file"""
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                emojis = json.load(f)

            print(f"Loaded {len(emojis)} emojis from {json_file_path}")
            return emojis

        except FileNotFoundError:
            raise ValueError(f"JSON file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    async def categorize_emoji(self, prompt: str) -> str:
        """Categorize emoji using Gemini AI with fallback"""
        try:
            category = await self.gemini_service.categorize_emoji_prompt(prompt)
            return category
        except Exception as e:
            print(
                f"Categorization failed for '{prompt}': {str(e)}, defaulting to 'Emotions'"
            )
            return "Emotions"

    def generate_emoji_id(self) -> str:
        """Generate a unique emoji ID"""
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(20))

    def get_current_timestamp(self) -> int:
        """Get current timestamp in milliseconds (same format as Firestore)"""
        return int(time.time() * 1000)

    async def create_firestore_emoji(
        self, json_emoji: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert JSON emoji to Firestore format"""
        try:
            name = json_emoji.get("name", "").strip()
            image_url = json_emoji.get("image_url", "").strip()

            if not name:
                raise ValueError(
                    f"Missing or empty 'name' field in emoji: {json_emoji}"
                )
            if not image_url:
                raise ValueError(
                    f"Missing or empty 'image_url' field in emoji: {json_emoji}"
                )

            emoji_id = self.generate_emoji_id()

            category = await self.categorize_emoji(name)

            firestore_emoji = {
                "category": category,
                "createdAt": self.get_current_timestamp(),
                "downloadCount": DEFAULT_DOWNLOAD_COUNT,
                "emojiID": emoji_id,
                "imageURL": image_url,
                "imageURLWithBackground": None,
                "predictionID": "scraper",
                "prompt": name,
                "userID": FIXED_USER_ID,
                "visibility": DEFAULT_VISIBILITY,
            }

            return firestore_emoji

        except Exception as e:
            print(f" Error creating Firestore emoji from {json_emoji}: {str(e)}")
            raise

    async def save_emoji_to_firestore(self, firestore_emoji: Dict[str, Any]) -> bool:
        """Save a single emoji to Firestore"""
        try:
            emoji_id = firestore_emoji["emojiID"]

            doc_ref = (
                self.db.collection("emojis")
                .document(FIXED_USER_ID)
                .collection("usersEmojis")
                .document(emoji_id)
            )

            doc_ref.set(firestore_emoji)

            return True

        except Exception as e:
            print(
                f"Error saving emoji {firestore_emoji.get('emojiID', 'unknown')} to Firestore: {str(e)}"
            )
            return False

    async def migrate_emojis_batch(
        self, emojis: List[Dict[str, Any]], batch_size: int = 50
    ) -> Dict[str, int]:
        """Migrate emojis in batches with progress tracking"""
        total_emojis = len(emojis)
        successful_migrations = 0
        failed_migrations = 0

        print(
            f"\n Starting migration of {total_emojis} emojis in batches of {batch_size}"
        )
        print("=" * 60)

        for i in range(0, total_emojis, batch_size):
            batch_end = min(i + batch_size, total_emojis)
            batch_emojis = emojis[i:batch_end]
            batch_num = (i // batch_size) + 1

            print(
                f"\n Processing batch {batch_num} ({i + 1}-{batch_end} of {total_emojis})..."
            )

            batch_successful = 0
            batch_failed = 0

            for j, json_emoji in enumerate(batch_emojis):
                try:
                    emoji_name = json_emoji.get("name", "Unknown")[:30]
                    print(
                        f"   [{i + j + 1:4d}/{total_emojis}] Processing: {emoji_name}..."
                    )

                    firestore_emoji = await self.create_firestore_emoji(json_emoji)

                    success = await self.save_emoji_to_firestore(firestore_emoji)

                    if success:
                        batch_successful += 1
                        print(f"Saved as '{firestore_emoji['category']}' category")
                    else:
                        batch_failed += 1

                except Exception as e:
                    batch_failed += 1
                    print(f"Failed to process emoji: {str(e)}")
                    continue

            successful_migrations += batch_successful
            failed_migrations += batch_failed

            print(
                f"Batch {batch_num} completed: {batch_successful} successful, {batch_failed} failed"
            )

            if batch_end < total_emojis:
                await asyncio.sleep(1)

        return {
            "total": total_emojis,
            "successful": successful_migrations,
            "failed": failed_migrations,
        }


async def migrate_emojis():
    """Main migration function"""
    try:
        print("Starting Emoji Migration to Firestore")
        print("=" * 50)

        print("Initializing Firebase...")
        initialize_firebase()
        print("Firebase initialized successfully")

        migration_service = EmojiMigrationService()

        json_file_path = project_root / "scripts" / "data" / "emojis.json"
        print(f"\nLoading emojis from {json_file_path}...")
        emojis = migration_service.load_emojis_from_json(str(json_file_path))

        if not emojis:
            print("No emojis found in JSON file")
            return

        print(f"\nTarget user ID: {FIXED_USER_ID}")
        print(
            f"Default values: downloadCount={DEFAULT_DOWNLOAD_COUNT}, visibility='{DEFAULT_VISIBILITY}'"
        )

        results = await migration_service.migrate_emojis_batch(emojis)

        print("\n" + "=" * 60)
        print("Migration Summary:")
        print(f"   • Total emojis processed: {results['total']}")
        print(f"   • Successfully migrated: {results['successful']}")
        print(f"   • Failed migrations: {results['failed']}")
        print(
            f"   • Success rate: {(results['successful'] / results['total'] * 100):.1f}%"
        )

        if results["successful"] > 0:
            print(
                f"\nSuccessfully migrated {results['successful']} emojis to Firestore!"
            )
            print(f"Location: emojis/{FIXED_USER_ID}/usersEmojis/")

        if results["failed"] > 0:
            print(
                f"\n{results['failed']} emojis failed to migrate. Check logs above for details."
            )

    except KeyboardInterrupt:
        print("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nMigration failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main function with user confirmation"""
    print("Emoji Migration to Firestore")
    print("This will migrate all emojis from emojis.json to Firestore")
    print(f"Target user ID: {FIXED_USER_ID}")

    print(f"\nData Mapping:")
    print(f"   • JSON 'name' → Firestore 'prompt'")
    print(f"   • JSON 'image_url' → Firestore 'imageURL'")
    print(f"   • Auto-generate: emojiID, category (via AI), createdAt")
    print(
        f"   • Fixed values: userID={FIXED_USER_ID}, downloadCount={DEFAULT_DOWNLOAD_COUNT}, visibility={DEFAULT_VISIBILITY}, predictionID='scraper'"
    )

    response = input(f"\nDo you want to proceed with the migration? (y/N): ")
    if response.lower() not in ["y", "yes"]:
        print("Migration cancelled by user")
        return

    await migrate_emojis()


if __name__ == "__main__":

    if not os.getenv("FIREBASE_CREDENTIALS_JSON") and not os.getenv(
        "FIREBASE_CREDENTIALS_PATH"
    ):
        print("Error: Firebase credentials not configured")
        print("   Please set either:")
        print(
            "   1. FIREBASE_CREDENTIALS_JSON environment variable with the full JSON content, or"
        )
        print(
            "   2. FIREBASE_CREDENTIALS_PATH environment variable pointing to your serviceAccountKey.json file"
        )
        sys.exit(1)

    if not os.getenv("GEMINI_API_KEY"):
        print("Error: Gemini AI credentials not configured")
        print("   Please set GEMINI_API_KEY environment variable")
        sys.exit(1)

    asyncio.run(main())
