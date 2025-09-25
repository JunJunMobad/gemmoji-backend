#!/usr/bin/env python3
"""
Count Total Emojis in Database

This script counts the total number of emojis across all users in the Firestore database.
It provides a breakdown by user and shows overall statistics.

Usage:
    python scripts/count_emojis.py

Environment variables required:
    FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from app.firebase_config import initialize_firebase, get_firestore_client


async def count_emojis_by_user(db):
    """Count emojis for each user individually"""
    try:
        print("Counting emojis by user...")

        user_counts = {}
        total_emojis = 0

        users_ref = db.collection("emojis")
        users = users_ref.stream()

        for user_doc in users:
            user_id = user_doc.id
            print(f"Counting emojis for user: {user_id}")

            user_emojis_ref = users_ref.document(user_id).collection("usersEmojis")
            user_emoji_count = len(list(user_emojis_ref.stream()))

            user_counts[user_id] = user_emoji_count
            total_emojis += user_emoji_count

            print(f"User {user_id}: {user_emoji_count} emojis")

        return user_counts, total_emojis

    except Exception as e:
        print(f"Error counting emojis by user: {str(e)}")
        raise


async def count_emojis_collection_group(db):
    """Count emojis using collection group query (faster for large datasets)"""
    try:
        print("Counting emojis using collection group query...")

        all_emojis_ref = db.collection_group("usersEmojis")

        total_count = 0
        batch_size = 1000

        last_doc = None
        while True:
            query = all_emojis_ref.limit(batch_size)
            if last_doc:
                query = query.start_after(last_doc)

            docs = list(query.stream())
            if not docs:
                break

            batch_count = len(docs)
            total_count += batch_count
            last_doc = docs[-1]

            print(
                f"Processed batch: {batch_count} emojis (Total so far: {total_count})"
            )

            if batch_count < batch_size:
                break

        return total_count

    except Exception as e:
        print(f"Error counting emojis with collection group: {str(e)}")
        raise


async def count_emojis_with_categories(db):
    """Count emojis and group by categories"""
    try:
        print("Counting emojis by category...")

        category_counts = defaultdict(int)
        visibility_counts = defaultdict(int)
        total_with_prediction_id = 0
        total_without_prediction_id = 0

        all_emojis_ref = db.collection_group("usersEmojis")

        batch_size = 500
        last_doc = None
        total_processed = 0

        while True:
            query = all_emojis_ref.limit(batch_size)
            if last_doc:
                query = query.start_after(last_doc)

            docs = list(query.stream())
            if not docs:
                break

            for doc in docs:
                data = doc.to_dict()

                category = data.get("category", "Unknown")
                category_counts[category] += 1

                visibility = data.get("visibility", "Unknown")
                visibility_counts[visibility] += 1

                if "predictionID" in data and data["predictionID"]:
                    total_with_prediction_id += 1
                else:
                    total_without_prediction_id += 1

            total_processed += len(docs)
            last_doc = docs[-1]

            print(f"Processed {len(docs)} emojis (Total: {total_processed})")

            if len(docs) < batch_size:
                break

        return {
            "categories": dict(category_counts),
            "visibility": dict(visibility_counts),
            "with_prediction_id": total_with_prediction_id,
            "without_prediction_id": total_without_prediction_id,
            "total": total_processed,
        }

    except Exception as e:
        print(f"Error counting emojis with categories: {str(e)}")
        raise


def print_results(user_counts, total_emojis, category_stats):
    """Print formatted results"""
    print("\n" + "=" * 60)
    print("EMOJI COUNT RESULTS")
    print("=" * 60)

    print(f"\nTOTAL EMOJIS: {total_emojis}")

    if user_counts:
        print(f"\nEMOJIS BY USER ({len(user_counts)} users):")
        print("-" * 40)
        for user_id, count in sorted(
            user_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"   {user_id}: {count:,} emojis")

    if category_stats:
        print(f"\nEMOJIS BY CATEGORY:")
        print("-" * 40)
        for category, count in sorted(
            category_stats["categories"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (count / category_stats["total"] * 100)
                if category_stats["total"] > 0
                else 0
            )
            print(f"   {category}: {count:,} emojis ({percentage:.1f}%)")

        print(f"\nEMOJIS BY VISIBILITY:")
        print("-" * 40)
        for visibility, count in sorted(
            category_stats["visibility"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (count / category_stats["total"] * 100)
                if category_stats["total"] > 0
                else 0
            )
            print(f"   {visibility}: {count:,} emojis ({percentage:.1f}%)")

        print(f"\nPREDICTION ID STATUS:")
        print("-" * 40)
        print(f"   With predictionID: {category_stats['with_prediction_id']:,} emojis")
        print(
            f"   Without predictionID: {category_stats['without_prediction_id']:,} emojis"
        )

    print("\n" + "=" * 60)


async def main():
    """Main function to count emojis"""
    try:
        print("Starting emoji count process...")

        initialize_firebase()
        db = get_firestore_client()

        print(" Firebase initialized successfully")

        print("\n" + "=" * 60)
        print("METHOD 1: Detailed count by user")
        print("=" * 60)
        user_counts, total_by_user = await count_emojis_by_user(db)

        print("\n" + "=" * 60)
        print("METHOD 2: Fast count using collection group")
        print("=" * 60)
        total_collection_group = await count_emojis_collection_group(db)

        print("\n" + "=" * 60)
        print("METHOD 3: Count with category and visibility breakdown")
        print("=" * 60)
        category_stats = await count_emojis_with_categories(db)

        print_results(user_counts, total_by_user, category_stats)

        if total_by_user == total_collection_group == category_stats["total"]:
            print(" All counting methods returned the same result!")
        else:
            print("Warning: Different counting methods returned different results:")
            print(f"   By user: {total_by_user}")
            print(f"   Collection group: {total_collection_group}")
            print(f"   With categories: {category_stats['total']}")

        print("\nEmoji counting completed successfully!")

    except Exception as e:
        print(f" Error in main: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
