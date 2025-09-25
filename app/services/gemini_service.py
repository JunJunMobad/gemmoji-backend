"""
Gemini AI service for emoji categorization
"""

import os
from typing import Optional
import google.generativeai as genai


class GeminiService:
    """Service class for Gemini AI operations"""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def categorize_emoji_prompt(self, prompt: str) -> str:
        """
        Categorize an emoji prompt using Gemini AI

        Args:
            prompt: The emoji prompt text to categorize

        Returns:
            Category string: "Animals", "Celebrities", "Memes", "Food", or "Emotions"
        """
        try:
            ai_prompt = f"""Categorize this emoji description into exactly one category:

                        Categories:
                        • Animals - pets, wildlife, creatures, insects
                        • Celebrities - famous people, actors, musicians, public figures  
                        • Memes - internet culture, viral content, popular references, funny characters
                        • Food - meals, snacks, drinks, cooking, eating
                        • Emotions - feelings, facial expressions, reactions, moods

                        Description: "{prompt}"

                        Return only the category name: Animals, Celebrities, Memes, Food, or Emotions."""

            response = self.model.generate_content(ai_prompt)
            category = response.text.strip()

            categories = ["Animals", "Celebrities", "Memes", "Food", "Emotions"]
            return category if category in categories else "Emotions"

        except Exception:
            return "Emotions"
