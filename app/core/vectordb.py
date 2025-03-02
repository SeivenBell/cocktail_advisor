import os
import numpy as np
import faiss
import pickle
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer

from app.config import VECTOR_DB_PATH, EMBEDDING_MODEL
from app.utils.data_processor import CocktailDataProcessor


class VectorDatabase:
    def __init__(self, model_name: str = EMBEDDING_MODEL, vector_db_path: Path = VECTOR_DB_PATH):
        self.model_name = model_name
        self.vector_db_path = vector_db_path
        self.embedding_model = None
        self.cocktail_index = None
        self.cocktail_data = None
        self.ingredient_index = None
        self.ingredient_data = None
        
        # Create the directory if it doesn't exist
        if not self.vector_db_path.exists():
            os.makedirs(self.vector_db_path)
            
        self._load_embedding_model()
        self._load_or_create_indexes()
        
    def _load_embedding_model(self) -> None:
        """Load the sentence transformer model for creating embeddings"""
        self.embedding_model = SentenceTransformer(self.model_name)
        
    def _load_or_create_indexes(self) -> None:
        """Load existing indexes or create new ones if they don't exist"""
        cocktail_index_path = self.vector_db_path / "cocktail_index.faiss"
        cocktail_data_path = self.vector_db_path / "cocktail_data.pkl"
        ingredient_index_path = self.vector_db_path / "ingredient_index.faiss"
        ingredient_data_path = self.vector_db_path / "ingredient_data.pkl"
        
        # Check if cocktail index exists
        if cocktail_index_path.exists() and cocktail_data_path.exists():
            self.cocktail_index = faiss.read_index(str(cocktail_index_path))
            with open(cocktail_data_path, 'rb') as f:
                self.cocktail_data = pickle.load(f)
        else:
            self._create_cocktail_index()
            
        # Check if ingredient index exists
        if ingredient_index_path.exists() and ingredient_data_path.exists():
            self.ingredient_index = faiss.read_index(str(ingredient_index_path))
            with open(ingredient_data_path, 'rb') as f:
                self.ingredient_data = pickle.load(f)
        else:
            self._create_ingredient_index()
    
    def _create_cocktail_index(self) -> None:
        """Create the cocktail vector index"""
        processor = CocktailDataProcessor()
        cocktails = processor.get_cocktails_for_embedding()
        
        # Create embeddings
        cocktail_texts = [cocktail['content'] for cocktail in cocktails]
        cocktail_embeddings = self.embedding_model.encode(cocktail_texts)
        
        # Create index
        dimension = cocktail_embeddings.shape[1]
        self.cocktail_index = faiss.IndexFlatL2(dimension)
        self.cocktail_index.add(np.array(cocktail_embeddings).astype('float32'))
        
        # Store data
        self.cocktail_data = cocktails
        
        # Save to disk
        faiss.write_index(self.cocktail_index, str(self.vector_db_path / "cocktail_index.faiss"))
        with open(self.vector_db_path / "cocktail_data.pkl", 'wb') as f:
            pickle.dump(self.cocktail_data, f)
            
    def _create_ingredient_index(self) -> None:
        """Create the ingredient vector index"""
        processor = CocktailDataProcessor()
        ingredients = processor.get_all_ingredients()
        
        # Create embeddings
        ingredient_embeddings = self.embedding_model.encode(ingredients)
        
        # Create index
        dimension = ingredient_embeddings.shape[1]
        self.ingredient_index = faiss.IndexFlatL2(dimension)
        self.ingredient_index.add(np.array(ingredient_embeddings).astype('float32'))
        
        # Store data
        self.ingredient_data = ingredients
        
        # Save to disk
        faiss.write_index(self.ingredient_index, str(self.vector_db_path / "ingredient_index.faiss"))
        with open(self.vector_db_path / "ingredient_data.pkl", 'wb') as f:
            pickle.dump(self.ingredient_data, f)
    
    def search_cocktails(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for cocktails similar to the query"""
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.cocktail_index.search(np.array(query_embedding).astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.cocktail_data):
                result = self.cocktail_data[idx].copy()
                result['score'] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                results.append(result)
        
        return results
    
    def search_ingredients(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for ingredients similar to the query"""
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.ingredient_index.search(np.array(query_embedding).astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.ingredient_data):
                ingredient = self.ingredient_data[idx]
                score = float(1.0 / (1.0 + distances[0][i]))
                results.append((ingredient, score))
        
        return results
    
    def get_similar_cocktails(self, cocktail_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get cocktails similar to the named cocktail"""
        processor = CocktailDataProcessor()
        cocktail = processor.get_cocktail_by_name(cocktail_name)
        
        if not cocktail:
            return []
        
        # Create a query from the cocktail information
        query = f"Cocktail with ingredients: {', '.join(cocktail['ingredients_list'])}"
        
        # Search using the query
        return self.search_cocktails(query, top_k)
    
    def get_cocktails_with_ingredients(self, ingredients: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Get cocktails containing the specified ingredients"""
        query = f"Cocktail with ingredients: {', '.join(ingredients)}"
        return self.search_cocktails(query, top_k)


# For testing the vector database
if __name__ == "__main__":
    db = VectorDatabase()
    
    # Test searching for cocktails
    results = db.search_cocktails("refreshing summer drink with citrus", 5)
    print("Cocktail search results:")
    for result in results:
        print(f"{result['name']} (Score: {result['score']:.4f})")
        
    # Test searching for ingredients
    results = db.search_ingredients("orange", 5)
    print("\nIngredient search results:")
    for ingredient, score in results:
        print(f"{ingredient} (Score: {score:.4f})")
    
    # Test getting similar cocktails
    results = db.get_similar_cocktails("Mojito", 5)
    print("\nSimilar cocktails to Mojito:")
    for result in results:
        print(f"{result['name']} (Score: {result['score']:.4f})")
