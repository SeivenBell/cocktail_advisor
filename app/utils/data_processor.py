import pandas as pd
import numpy as np
from pathlib import Path
import re
import json
from typing import List, Dict, Any, Tuple, Optional

from app.config import COCKTAILS_CSV_PATH


class CocktailDataProcessor:
    def __init__(self, csv_path: Path = COCKTAILS_CSV_PATH):
        self.csv_path = csv_path
        self.cocktails_df = None
        self.load_data()
        
    def load_data(self) -> None:
        """Load cocktail data from CSV file"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Cocktail data file not found at {self.csv_path}")
        
        self.cocktails_df = pd.read_csv(self.csv_path)
        self._clean_data()
        
    def _clean_data(self) -> None:
        """Clean and preprocess the cocktail data"""
        # Handle missing values
        self.cocktails_df = self.cocktails_df.fillna('')
        
        # Clean column names
        self.cocktails_df.columns = [col.lower().strip() for col in self.cocktails_df.columns]
        
        # Ensure we have the expected columns
        required_columns = ['name', 'ingredients', 'garnish', 'preparation', 'glass']
        for col in required_columns:
            if col not in self.cocktails_df.columns:
                # Try to find an alternative column
                for existing_col in self.cocktails_df.columns:
                    if col in existing_col:
                        self.cocktails_df[col] = self.cocktails_df[existing_col]
                        break
                else:
                    self.cocktails_df[col] = ''
        
        # Extract alcoholic status
        self.cocktails_df['is_alcoholic'] = ~self.cocktails_df['ingredients'].str.lower().str.contains('non-alcoholic|non alcoholic|alcohol-free|alcohol free|virgin', case=False)
        
        # Process ingredients into a list
        self.cocktails_df['ingredients_list'] = self.cocktails_df['ingredients'].apply(self._extract_ingredients)
        
    def _extract_ingredients(self, ingredients_text: str) -> List[str]:
        """Extract individual ingredients from ingredients text"""
        if not ingredients_text:
            return []
        
        # Split by common delimiters
        ingredients = re.split(r'[,;\n]', ingredients_text)
        
        # Clean up each ingredient
        clean_ingredients = []
        for ingredient in ingredients:
            ingredient = ingredient.strip()
            if ingredient:
                # Remove quantities and measurements
                ingredient = re.sub(r'^\d+\s*(?:oz|ml|cl|dash|dashes|teaspoon|tablespoon|tsp|tbsp|shot|shots|part|parts|pinch|drops|splash|sprigs?|slices?|wedges?)\s+(?:of\s+)?', '', ingredient, flags=re.IGNORECASE)
                ingredient = re.sub(r'^\d+[/\d\s.]*\s+(?:of\s+)?', '', ingredient)
                
                # Remove any remaining parentheses and their contents
                ingredient = re.sub(r'\([^)]*\)', '', ingredient)
                
                ingredient = ingredient.strip()
                if ingredient:
                    clean_ingredients.append(ingredient.lower())
        
        return clean_ingredients
    
    def get_cocktails_containing(self, ingredient: str) -> pd.DataFrame:
        """Get cocktails containing a specific ingredient"""
        ingredient = ingredient.lower()
        mask = self.cocktails_df['ingredients_list'].apply(
            lambda ingredients: any(ingredient in ing for ing in ingredients)
        )
        return self.cocktails_df[mask]
    
    def get_non_alcoholic_cocktails(self) -> pd.DataFrame:
        """Get all non-alcoholic cocktails"""
        return self.cocktails_df[~self.cocktails_df['is_alcoholic']]
    
    def get_cocktail_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a cocktail by name"""
        name = name.lower()
        result = self.cocktails_df[self.cocktails_df['name'].str.lower() == name]
        if result.empty:
            # Try fuzzy matching
            result = self.cocktails_df[self.cocktails_df['name'].str.lower().str.contains(name, case=False)]
            
        if not result.empty:
            return result.iloc[0].to_dict()
        return None
    
    def get_cocktails_for_embedding(self) -> List[Dict[str, Any]]:
        """Prepare cocktail data for embedding"""
        cocktails = []
        for _, row in self.cocktails_df.iterrows():
            cocktail = {
                'id': row.name,  # This is the index in pandas DataFrame
                'name': row['name'],
                'ingredients': ', '.join(row['ingredients_list']),
                'garnish': row['garnish'],
                'preparation': row['preparation'],
                'glass': row['glass'],
                'is_alcoholic': row['is_alcoholic'],
                'content': f"Cocktail: {row['name']}\n"
                          f"Ingredients: {row['ingredients']}\n"
                          f"Garnish: {row['garnish']}\n"
                          f"Preparation: {row['preparation']}\n"
                          f"Glass: {row['glass']}\n"
            }
            cocktails.append(cocktail)
        return cocktails
    
    def get_all_ingredients(self) -> List[str]:
        """Get a list of all unique ingredients"""
        all_ingredients = []
        for ingredients in self.cocktails_df['ingredients_list']:
            all_ingredients.extend(ingredients)
        return list(set(all_ingredients))


# For testing the data processor
if __name__ == "__main__":
    processor = CocktailDataProcessor()
    print(f"Loaded {len(processor.cocktails_df)} cocktails")
    
    # Test getting cocktails with lemon
    lemon_cocktails = processor.get_cocktails_containing("lemon")
    print(f"Found {len(lemon_cocktails)} cocktails containing lemon")
    print(lemon_cocktails['name'].tolist()[:5])
    
    # Test getting non-alcoholic cocktails
    non_alcoholic = processor.get_non_alcoholic_cocktails()
    print(f"Found {len(non_alcoholic)} non-alcoholic cocktails")
    
    # Test getting all ingredients
    all_ingredients = processor.get_all_ingredients()
    print(f"Found {len(all_ingredients)} unique ingredients")
