import os
import json
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from app.config import USER_MEMORY_PATH


class UserMemory:
    def __init__(self, memory_path: Path = USER_MEMORY_PATH, user_id: str = "default_user"):
        self.memory_path = memory_path
        self.user_id = user_id
        self.user_memory_file = self.memory_path / f"{user_id}_memory.json"
        self.favorite_ingredients: Set[str] = set()
        self.favorite_cocktails: Set[str] = set()
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Create the directory if it doesn't exist
        if not self.memory_path.exists():
            os.makedirs(self.memory_path)
            
        self._load_memory()
    
    def _load_memory(self) -> None:
        """Load user memory from file if it exists"""
        if self.user_memory_file.exists():
            try:
                with open(self.user_memory_file, 'r') as f:
                    data = json.load(f)
                    self.favorite_ingredients = set(data.get('favorite_ingredients', []))
                    self.favorite_cocktails = set(data.get('favorite_cocktails', []))
                    self.conversation_history = data.get('conversation_history', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading user memory: {e}")
                # Initialize with empty data
                self._save_memory()
    
    def _save_memory(self) -> None:
        """Save user memory to file"""
        data = {
            'favorite_ingredients': list(self.favorite_ingredients),
            'favorite_cocktails': list(self.favorite_cocktails),
            'conversation_history': self.conversation_history
        }
        
        try:
            with open(self.user_memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving user memory: {e}")
    
    def add_favorite_ingredient(self, ingredient: str) -> None:
        """Add an ingredient to user's favorites"""
        ingredient = ingredient.lower().strip()
        self.favorite_ingredients.add(ingredient)
        self._save_memory()
    
    def remove_favorite_ingredient(self, ingredient: str) -> bool:
        """Remove an ingredient from user's favorites, return True if it existed"""
        ingredient = ingredient.lower().strip()
        if ingredient in self.favorite_ingredients:
            self.favorite_ingredients.remove(ingredient)
            self._save_memory()
            return True
        return False
    
    def add_favorite_cocktail(self, cocktail: str) -> None:
        """Add a cocktail to user's favorites"""
        cocktail = cocktail.strip()
        self.favorite_cocktails.add(cocktail)
        self._save_memory()
    
    def remove_favorite_cocktail(self, cocktail: str) -> bool:
        """Remove a cocktail from user's favorites, return True if it existed"""
        cocktail = cocktail.strip()
        if cocktail in self.favorite_cocktails:
            self.favorite_cocktails.remove(cocktail)
            self._save_memory()
            return True
        return False
    
    def add_to_conversation_history(self, role: str, content: str) -> None:
        """Add a message to the conversation history"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only the last 50 messages
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
            
        self._save_memory()
    
    def get_favorite_ingredients(self) -> List[str]:
        """Get user's favorite ingredients"""
        return list(self.favorite_ingredients)
    
    def get_favorite_cocktails(self) -> List[str]:
        """Get user's favorite cocktails"""
        return list(self.favorite_cocktails)
    
    def get_recent_conversation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent conversation messages"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def detect_favorite_ingredients(self, message: str) -> List[str]:
        """
        Detect if the user is expressing favorite ingredients in their message
        Returns a list of detected ingredients
        """
        # Patterns to detect favorite ingredients
        patterns = [
            r"I (?:really )?like(?: to use)? (.+?)(?: in my (?:drinks|cocktails))?[.!]",
            r"I (?:really )?love(?: to use)? (.+?)(?: in my (?:drinks|cocktails))?[.!]",
            r"My favorite (?:ingredient|ingredients) (?:is|are) (.+?)[.!]",
            r"I prefer (?:to use )?(.+?)(?: in my (?:drinks|cocktails))?[.!]",
            r"I enjoy (?:using )?(.+?)(?: in my (?:drinks|cocktails))?[.!]"
        ]
        
        detected_ingredients = []
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                # Split by commas or 'and' to get individual ingredients
                ingredients = re.split(r',|\sand\s', match)
                detected_ingredients.extend([ing.strip().lower() for ing in ingredients if ing.strip()])
                
        return detected_ingredients
    
    def detect_favorite_cocktails(self, message: str) -> List[str]:
        """
        Detect if the user is expressing favorite cocktails in their message
        Returns a list of detected cocktails
        """
        # Patterns to detect favorite cocktails
        patterns = [
            r"I (?:really )?like(?: to drink)? (?:the )?(.+?)(?: cocktail)?[.!]",
            r"I (?:really )?love(?: to drink)? (?:the )?(.+?)(?: cocktail)?[.!]",
            r"My favorite (?:cocktail|drink) is (?:the )?(.+?)[.!]",
            r"I prefer (?:to drink )?(?:the )?(.+?)(?: cocktail)?[.!]",
            r"I enjoy (?:drinking )?(?:the )?(.+?)(?: cocktail)?[.!]"
        ]
        
        detected_cocktails = []
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                # Split by commas or 'and' to get individual cocktails
                cocktails = re.split(r',|\sand\s', match)
                detected_cocktails.extend([cocktail.strip() for cocktail in cocktails if cocktail.strip()])
                
        return detected_cocktails
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message to detect preferences and update memory
        Returns a dict with detected preferences
        """
        result = {
            'new_favorite_ingredients': [],
            'new_favorite_cocktails': []
        }
        
        # Detect and process favorite ingredients
        detected_ingredients = self.detect_favorite_ingredients(message)
        for ingredient in detected_ingredients:
            if ingredient not in self.favorite_ingredients:
                self.add_favorite_ingredient(ingredient)
                result['new_favorite_ingredients'].append(ingredient)
        
        # Detect and process favorite cocktails
        detected_cocktails = self.detect_favorite_cocktails(message)
        for cocktail in detected_cocktails:
            if cocktail not in self.favorite_cocktails:
                self.add_favorite_cocktail(cocktail)
                result['new_favorite_cocktails'].append(cocktail)
        
        # Add the message to conversation history
        self.add_to_conversation_history('user', message)
        
        return result