import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

db: Optional[firestore.Client] = None


def initialize_firebase() -> None:
    global db

    if firebase_admin._apps:
        db = firestore.client()
        return

    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ Firebase initialized (from environment variable)")
            return
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in FIREBASE_CREDENTIALS_JSON: {str(e)}")

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not cred_path or not os.path.exists(cred_path):
        raise ValueError(
            "Firebase credentials not found. Please set either:\n"
            "1. FIREBASE_CREDENTIALS_JSON environment variable with the full JSON content, or\n"
            "2. FIREBASE_CREDENTIALS_PATH environment variable pointing to your serviceAccountKey.json file"
        )

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

    db = firestore.client()
    print("✅ Firebase initialized (from file)")


def get_firestore_client() -> firestore.Client:
    if db is None:
        raise RuntimeError("Firebase not initialized.")
    return db
