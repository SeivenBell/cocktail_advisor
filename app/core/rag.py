from typing import List, Dict, Any, Optional, Tuple
import re
from app.core.llm import LLMManager
from app.core.vectordb import VectorDatabase
from app.core.memory import UserMemory
from app.utils.data_processor import CocktailDataProcessor


class RAGSystem:
    def __init__(self):
        self.llm = LLMManager()
        self.vectordb = VectorDatabase()
        self.data_processor = CocktailDataProcessor()

    def identify_query_type(self, query: str) -> str:
        """
        Identify the type of query to determine how to process it
        Returns: 'ingredient_query', 'cocktail_query', 'recommendation', 'preference', or 'general'
        """
        # Convert query to lowercase for case-insensitive matching
        query_lower = query.lower()

        # Patterns for different query types
        ingredient_patterns = [
            r"cocktails? (?:with|containing|that (?:has|have)) (.+)",
            r"(?:list|show|tell me|what are) (?:some|the|all)? cocktails? (?:with|containing|that (?:has|have)) (.+)",
            r"what (?:cocktails|drinks) (?:can I make|have|contain) (?:with|using) (.+)",
        ]

        cocktail_patterns = [
            r"(?:how|tell me how) to make (?:a|an) (.+)",
            r"(?:what is|what's) (?:a|an) (.+)",
            r"(?:recipe|ingredients) for (?:a|an) (.+)",
        ]

        recommendation_patterns = [
            r"recommend (?:a|some) cocktails?",
            r"(?:suggest|give me) (?:a|some) cocktails?",
            r"what cocktail should I (?:make|try|drink)",
            r"similar to (.+)",
            r"like (?:a|an) (.+)",
        ]

        preference_patterns = [
            r"(?:my|I) (?:like|love|prefer|favorite|enjoy)",
            r"(?:remember|save|store) (?:this|these|my) (?:preference|ingredient|cocktail)",
            r"what are my (?:favorite|preferred) (?:ingredients|cocktails)",
        ]

        # Check each pattern type
        for pattern in ingredient_patterns:
            if re.search(pattern, query_lower):
                return "ingredient_query"

        for pattern in cocktail_patterns:
            if re.search(pattern, query_lower):
                return "cocktail_query"

        for pattern in recommendation_patterns:
            if re.search(pattern, query_lower):
                return "recommendation"

        for pattern in preference_patterns:
            if re.search(pattern, query_lower):
                return "preference"

        # Default to general query if no patterns match
        return "general"

    def extract_ingredients_from_query(self, query: str) -> List[str]:
        """Extract ingredients mentioned in the query"""
        # Patterns to match ingredients
        patterns = [
            r"with ([^?.,!]+)",
            r"containing ([^?.,!]+)",
            r"that (?:has|have) ([^?.,!]+)",
            r"using ([^?.,!]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Split by commas and 'and' to get individual ingredients
                ingredients_text = match.group(1)
                ingredients = re.split(r",|\sand\s", ingredients_text)
                return [ing.strip().lower() for ing in ingredients if ing.strip()]

        return []

    def extract_cocktail_from_query(self, query: str) -> Optional[str]:
        """Extract cocktail name mentioned in the query"""
        # Patterns to match cocktail names
        patterns = [
            r"how to make (?:a|an) ([^?.,!]+)",
            r"(?:what is|what's) (?:a|an) ([^?.,!]+)",
            r"recipe for (?:a|an) ([^?.,!]+)",
            r"similar to ([^?.,!]+)",
            r"like (?:a|an) ([^?.,!]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def process_ingredient_query(self, query: str, user_memory: UserMemory) -> str:
        """Process a query about cocktails with specific ingredients"""
        ingredients = self.extract_ingredients_from_query(query)

        if not ingredients:
            return "I couldn't identify which ingredients you're asking about. Could you specify which ingredients you're interested in?"

        # Check if asking for non-alcoholic cocktails
        is_non_alcoholic = (
            "non-alcoholic" in query.lower() or "non alcoholic" in query.lower()
        )

        # Get relevant cocktails
        relevant_cocktails = []
        for ingredient in ingredients:
            matching_cocktails = self.data_processor.get_cocktails_containing(
                ingredient
            )
            if is_non_alcoholic:
                matching_cocktails = matching_cocktails[
                    ~matching_cocktails["is_alcoholic"]
                ]
            relevant_cocktails.append(matching_cocktails)

        # Find intersection of matching cocktails if multiple ingredients
        if len(relevant_cocktails) > 1:
            result_df = relevant_cocktails[0]
            for df in relevant_cocktails[1:]:
                result_df = result_df.merge(df, how="inner")
        elif len(relevant_cocktails) == 1:
            result_df = relevant_cocktails[0]
        else:
            result_df = None

        # Determine number of cocktails to return
        limit = 5  # Default
        match = re.search(r"(\d+)\s+cocktails", query, re.IGNORECASE)
        if match:
            limit = int(match.group(1))

        # Build response
        if result_df is not None and not result_df.empty:
            cocktail_names = result_df["name"].tolist()[:limit]
            ingredients_str = ", ".join(ingredients)

            # Format response for RAG - without using newlines in f-string expressions
            context = (
                f"\nFound {len(result_df)} cocktails containing {ingredients_str}.\n"
                f"Here are {min(limit, len(cocktail_names))} of them:\n\n"
            )

            # Add cocktail names without using newlines in f-string expressions
            for name in cocktail_names:
                context += f"- {name}\n"

            # Get response from LLM
            system_prompt = (
                "You are a knowledgeable bartender assistant. Provide helpful, conversational "
                "responses about cocktails. Use the context provided to answer the user's question.\n\n"
                f"Context:\n{context}"
            )
            response = self.llm.generate_response(query, system_prompt)

            # Update conversation history
            user_memory.add_to_conversation_history("assistant", response)

            return response

        return f"I couldn't find any cocktails containing {', '.join(ingredients)}. Would you like to try different ingredients?"

    def process_cocktail_query(self, query: str, user_memory: UserMemory) -> str:
        """Process a query about a specific cocktail"""
        cocktail_name = self.extract_cocktail_from_query(query)

        if not cocktail_name:
            return "I couldn't identify which cocktail you're asking about. Could you specify the name of the cocktail?"

        # Get cocktail information
        cocktail = self.data_processor.get_cocktail_by_name(cocktail_name)

        if cocktail:
            # Format context for RAG - without using newlines in f-string expressions
            context = (
                f"\nCocktail: {cocktail['name']}\n"
                f"Ingredients: {cocktail['ingredients']}\n"
                f"Preparation: {cocktail['preparation']}\n"
                f"Glass: {cocktail['glass']}\n"
                f"Garnish: {cocktail['garnish']}\n"
            )

            # Get response from LLM
            system_prompt = (
                "You are a knowledgeable bartender assistant. Provide helpful, conversational "
                "responses about cocktails. Use the context provided to answer the user's question.\n\n"
                f"Context:\n{context}"
            )
            response = self.llm.generate_response(query, system_prompt)

            # Update conversation history
            user_memory.add_to_conversation_history("assistant", response)

            return response

        return f"I couldn't find information about {cocktail_name}. Could you check the spelling or try a different cocktail?"

    def process_recommendation_query(self, query: str, user_memory: UserMemory) -> str:
        """Process a query asking for cocktail recommendations"""
        # Check if it's a similarity recommendation
        cocktail_name = self.extract_cocktail_from_query(query)

        if (
            "favorite" in query.lower()
            or "favourites" in query.lower()
            or "prefer" in query.lower()
        ):
            # Recommendation based on favorite ingredients
            favorite_ingredients = user_memory.get_favorite_ingredients()

            if not favorite_ingredients:
                return "I don't have any information about your favorite ingredients yet. Would you like to tell me what ingredients you enjoy?"

            # Get cocktails with favorite ingredients
            similar_cocktails = self.vectordb.get_cocktails_with_ingredients(
                favorite_ingredients
            )

            # Format context for RAG - without using newlines in f-string expressions
            context = (
                f"\nBased on your favorite ingredients ({', '.join(favorite_ingredients)}), "
                f"here are some cocktails you might enjoy:\n\n"
            )

            # Add cocktail information without using newlines in f-string expressions
            for c in similar_cocktails[:5]:
                context += f"- {c['name']}: {c['ingredients']}\n"

            # Get response from LLM
            system_prompt = (
                "You are a knowledgeable bartender assistant. Provide helpful, conversational recommendations "
                "based on the user's preferences. Use the context provided to personalize your recommendations.\n\n"
                f"Context:\n{context}"
            )
            response = self.llm.generate_response(query, system_prompt)

            # Update conversation history
            user_memory.add_to_conversation_history("assistant", response)

            return response

        elif cocktail_name:
            # Recommendation based on similar cocktail
            similar_cocktails = self.vectordb.get_similar_cocktails(cocktail_name)

            if not similar_cocktails:
                return f"I couldn't find {cocktail_name} or any similar cocktails. Could you check the spelling or try a different cocktail?"

            # Format context for RAG - without using newlines in f-string expressions
            context = f'\nBased on the cocktail "{cocktail_name}", here are some similar cocktails you might enjoy:\n\n'

            # Add similar cocktails without using newlines in f-string expressions
            for c in similar_cocktails[:5]:
                if c["name"].lower() != cocktail_name.lower():
                    context += f"- {c['name']}: {c['ingredients']}\n"

            # Get response from LLM
            system_prompt = (
                "You are a knowledgeable bartender assistant. Provide helpful, conversational recommendations "
                "for cocktails similar to what the user requested. Use the context provided to inform your recommendations.\n\n"
                f"Context:\n{context}"
            )
            response = self.llm.generate_response(query, system_prompt)

            # Update conversation history
            user_memory.add_to_conversation_history("assistant", response)

            return response

        # General recommendation
        # Get random popular cocktails
        popular_cocktails = self.data_processor.cocktails_df.sample(5).to_dict(
            "records"
        )

        # Format context for RAG - without using newlines in f-string expressions
        context = "\nHere are some popular cocktail recommendations:\n\n"

        # Add cocktail recommendations without using newlines in f-string expressions
        for c in popular_cocktails:
            context += f"- {c['name']}: {c['ingredients']}\n"

        # Get response from LLM
        system_prompt = (
            "You are a knowledgeable bartender assistant. Provide helpful, conversational recommendations "
            "for cocktails. Use the context provided to inform your recommendations.\n\n"
            f"Context:\n{context}"
        )
        response = self.llm.generate_response(query, system_prompt)

        # Update conversation history
        user_memory.add_to_conversation_history("assistant", response)

        return response

    def process_preference_query(self, query: str, user_memory: UserMemory) -> str:
        """Process a query about user preferences"""
        if "what are my" in query.lower() or "tell me my" in query.lower():
            # Get user's favorite ingredients and cocktails
            favorite_ingredients = user_memory.get_favorite_ingredients()
            favorite_cocktails = user_memory.get_favorite_cocktails()

            # Format context for RAG - avoid using newlines in f-string expressions
            context = "Here are your preferences:\n"

            if favorite_ingredients:
                context += f"\nFavorite ingredients: {', '.join(favorite_ingredients)}"
            else:
                context += "\nYou haven't told me about any favorite ingredients yet."

            if favorite_cocktails:
                context += f"\nFavorite cocktails: {', '.join(favorite_cocktails)}"
            else:
                context += "\nYou haven't told me about any favorite cocktails yet."

            # Get response from LLM
            system_prompt = (
                "You are a knowledgeable bartender assistant. Provide helpful, conversational responses about "
                "the user's preferences. Use the context provided to personalize your response.\n\n"
                f"Context:\n{context}"
            )
            response = self.llm.generate_response(query, system_prompt)

            # Update conversation history
            user_memory.add_to_conversation_history("assistant", response)

            return response

        # Process the message to detect and save preferences
        preference_result = user_memory.process_user_message(query)

        if (
            preference_result["new_favorite_ingredients"]
            or preference_result["new_favorite_cocktails"]
        ):
            # Format context for RAG - avoid using newlines in f-string expressions
            context = "I've updated your preferences:\n"

            if preference_result["new_favorite_ingredients"]:
                context += f"\nAdded favorite ingredients: {', '.join(preference_result['new_favorite_ingredients'])}"

            if preference_result["new_favorite_cocktails"]:
                context += f"\nAdded favorite cocktails: {', '.join(preference_result['new_favorite_cocktails'])}"

            # Get response from LLM
            system_prompt = (
                "You are a knowledgeable bartender assistant. Acknowledge that you've saved the user's preferences "
                "and provide a friendly response. Use the context provided to personalize your response.\n\n"
                f"Context:\n{context}"
            )
            response = self.llm.generate_response(query, system_prompt)

            # Update conversation history
            user_memory.add_to_conversation_history("assistant", response)

            return response

        # If no clear preference was detected
        return self.process_general_query(query, user_memory)

    def process_general_query(self, query: str, user_memory: UserMemory) -> str:
        """Process a general query about cocktails"""
        # Try to find relevant cocktail information
        relevant_cocktails = self.vectordb.search_cocktails(query, top_k=3)

        # Format context for RAG - avoid using newlines in f-string expressions
        context = "Here's some information that might help with your question:\n\n"

        if relevant_cocktails:
            for cocktail in relevant_cocktails:
                context += f"Cocktail: {cocktail['name']}\n"
                context += f"Ingredients: {cocktail['ingredients']}\n"
                context += f"Preparation: {cocktail['preparation']}\n"
                if cocktail["garnish"]:
                    context += f"Garnish: {cocktail['garnish']}\n"
                context += "\n"

        # Add user preferences to context
        favorite_ingredients = user_memory.get_favorite_ingredients()
        if favorite_ingredients:
            context += f"Your favorite ingredients: {', '.join(favorite_ingredients)}\n"

        # Get response from LLM
        system_prompt = (
            "You are a knowledgeable bartender assistant. Provide helpful, conversational responses about cocktails. "
            "If the user's query is not specifically about cocktails, still try to be helpful but gently steer the "
            "conversation back to cocktails when appropriate.\n\n"
            f"Context:\n{context}"
        )
        response = self.llm.generate_response(query, system_prompt)

        # Process the message to detect and save preferences
        user_memory.process_user_message(query)

        # Update conversation history
        user_memory.add_to_conversation_history("assistant", response)

        return response

    def generate_response(self, query: str, user_memory: UserMemory) -> str:
        """
        Main method to generate a response to a user query

        Args:
            query: The user's question
            user_memory: The user's memory object

        Returns:
            The generated response
        """
        # First, detect any preferences in the query and update memory
        user_memory.process_user_message(query)

        # Identify the type of query
        query_type = self.identify_query_type(query)

        # Process based on query type
        if query_type == "ingredient_query":
            return self.process_ingredient_query(query, user_memory)
        elif query_type == "cocktail_query":
            return self.process_cocktail_query(query, user_memory)
        elif query_type == "recommendation":
            return self.process_recommendation_query(query, user_memory)
        elif query_type == "preference":
            return self.process_preference_query(query, user_memory)
        else:
            return self.process_general_query(query, user_memory)
