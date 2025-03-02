from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.rag import RAGSystem
from app.core.memory import UserMemory
from app.utils.data_processor import CocktailDataProcessor

router = APIRouter()
rag_system = RAGSystem()
data_processor = CocktailDataProcessor()


# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    message: str
    user_id: str = "default_user"


class ChatResponse(BaseModel):
    response: str
    detected_preferences: Dict[str, List[str]] = {"ingredients": [], "cocktails": []}


class CocktailQuery(BaseModel):
    ingredient: str
    limit: int = 5
    alcoholic_only: bool = False


class CocktailList(BaseModel):
    cocktails: List[Dict[str, Any]]


class RecommendationQuery(BaseModel):
    similar_to: Optional[str] = None
    ingredients: List[str] = []
    user_id: str = "default_user"
    limit: int = 5


class PreferenceQuery(BaseModel):
    user_id: str = "default_user"


class PreferenceUpdate(BaseModel):
    user_id: str = "default_user"
    ingredients: Optional[List[str]] = None
    cocktails: Optional[List[str]] = None


class PreferenceResponse(BaseModel):
    user_id: str
    favorite_ingredients: List[str]
    favorite_cocktails: List[str]


# Get user memory object
def get_user_memory(user_id: str = "default_user") -> UserMemory:
    return UserMemory(user_id=user_id)


# Chat endpoint
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """
    Process a chat message and return a response
    """
    user_memory = get_user_memory(request.user_id)
    response = rag_system.generate_response(request.message, user_memory)
    
    # Get new preferences that were detected
    detected_preferences = {
        "ingredients": [],
        "cocktails": []
    }
    
    # Check for new ingredients that were detected
    all_ingredients = user_memory.get_favorite_ingredients()
    detected_ingredients = user_memory.detect_favorite_ingredients(request.message)
    for ingredient in detected_ingredients:
        if ingredient in all_ingredients:
            detected_preferences["ingredients"].append(ingredient)
    
    # Check for new cocktails that were detected
    all_cocktails = user_memory.get_favorite_cocktails()
    detected_cocktails = user_memory.detect_favorite_cocktails(request.message)
    for cocktail in detected_cocktails:
        if cocktail in all_cocktails:
            detected_preferences["cocktails"].append(cocktail)
    
    return ChatResponse(
        response=response,
        detected_preferences=detected_preferences
    )


# Cocktail query endpoints
@router.post("/cocktails/by-ingredient", response_model=CocktailList)
async def get_cocktails_by_ingredient(query: CocktailQuery):
    """
    Get cocktails containing a specific ingredient
    """
    matching_cocktails = data_processor.get_cocktails_containing(query.ingredient)
    
    if not query.alcoholic_only:
        # Include both alcoholic and non-alcoholic
        pass
    else:
        # Filter for alcoholic only
        matching_cocktails = matching_cocktails[matching_cocktails['is_alcoholic']]
    
    # Convert to list of dictionaries
    result = matching_cocktails.head(query.limit).to_dict('records')
    
    return CocktailList(cocktails=result)


@router.post("/cocktails/non-alcoholic", response_model=CocktailList)
async def get_non_alcoholic_cocktails():
    """
    Get all non-alcoholic cocktails
    """
    non_alcoholic = data_processor.get_non_alcoholic_cocktails()
    result = non_alcoholic.to_dict('records')
    
    return CocktailList(cocktails=result)


@router.get("/cocktails/{name}", response_model=Dict[str, Any])
async def get_cocktail_by_name(name: str):
    """
    Get a specific cocktail by name
    """
    cocktail = data_processor.get_cocktail_by_name(name)
    
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")
    
    return cocktail


# Recommendation endpoints
@router.post("/recommendations", response_model=CocktailList)
async def get_recommendations(query: RecommendationQuery):
    """
    Get cocktail recommendations based on user preferences or similar cocktails
    """
    if query.similar_to:
        # Get similar cocktails
        similar_cocktails = rag_system.vectordb.get_similar_cocktails(query.similar_to, query.limit)
        return CocktailList(cocktails=similar_cocktails)
    
    elif query.ingredients:
        # Get cocktails with specific ingredients
        cocktails = rag_system.vectordb.get_cocktails_with_ingredients(query.ingredients, query.limit)
        return CocktailList(cocktails=cocktails)
    
    else:
        # Get recommendations based on user preferences
        user_memory = get_user_memory(query.user_id)
        favorite_ingredients = user_memory.get_favorite_ingredients()
        
        if not favorite_ingredients:
            # No preferences, return popular cocktails
            popular_cocktails = data_processor.cocktails_df.sample(query.limit).to_dict('records')
            return CocktailList(cocktails=popular_cocktails)
        
        # Get cocktails with favorite ingredients
        cocktails = rag_system.vectordb.get_cocktails_with_ingredients(favorite_ingredients, query.limit)
        return CocktailList(cocktails=cocktails)


# User preference endpoints
@router.get("/preferences/{user_id}", response_model=PreferenceResponse)
async def get_user_preferences(user_id: str):
    """
    Get a user's saved preferences
    """
    user_memory = get_user_memory(user_id)
    
    return PreferenceResponse(
        user_id=user_id,
        favorite_ingredients=user_memory.get_favorite_ingredients(),
        favorite_cocktails=user_memory.get_favorite_cocktails()
    )


@router.post("/preferences/update", response_model=PreferenceResponse)
async def update_user_preferences(update: PreferenceUpdate):
    """
    Update a user's preferences
    """
    user_memory = get_user_memory(update.user_id)
    
    # Update ingredients if provided
    if update.ingredients is not None:
        for ingredient in update.ingredients:
            user_memory.add_favorite_ingredient(ingredient)
    
    # Update cocktails if provided
    if update.cocktails is not None:
        for cocktail in update.cocktails:
            user_memory.add_favorite_cocktail(cocktail)
    
    return PreferenceResponse(
        user_id=update.user_id,
        favorite_ingredients=user_memory.get_favorite_ingredients(),
        favorite_cocktails=user_memory.get_favorite_cocktails()
    )


@router.post("/preferences/remove", response_model=PreferenceResponse)
async def remove_user_preferences(update: PreferenceUpdate):
    """
    Remove preferences from a user's profile
    """
    user_memory = get_user_memory(update.user_id)
    
    # Remove ingredients if provided
    if update.ingredients is not None:
        for ingredient in update.ingredients:
            user_memory.remove_favorite_ingredient(ingredient)
    
    # Remove cocktails if provided
    if update.cocktails is not None:
        for cocktail in update.cocktails:
            user_memory.remove_favorite_cocktail(cocktail)
    
    return PreferenceResponse(
        user_id=update.user_id,
        favorite_ingredients=user_memory.get_favorite_ingredients(),
        favorite_cocktails=user_memory.get_favorite_cocktails()
    )