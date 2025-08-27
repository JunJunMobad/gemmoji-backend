import os
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

db: Optional[firestore.Client] = None

def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK"""
    global db
    
    if firebase_admin._apps:
        db = firestore.client()
        return
    
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not cred_path or not os.path.exists(cred_path):
        raise ValueError(
            "Firebase credentials file not found. "
            "Please set FIREBASE_CREDENTIALS_PATH environment variable "
            "pointing to your serviceAccountKey.json file"
        )
    
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    print("✅ Firebase initialized")

def get_firestore_client() -> firestore.Client:
    if db is None:
        raise RuntimeError("Firebase not initialized.")
    return db