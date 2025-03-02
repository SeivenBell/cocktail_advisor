from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Any, Optional

from app.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class LLMManager:
    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        model: str = LLM_MODEL,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the LLM client"""
        return ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response from the LLM

        Args:
            user_input: The user's message
            system_prompt: The system prompt to guide the LLM
            chat_history: Optional chat history in the format [{"role": "user"|"assistant", "content": "message"}]

        Returns:
            The LLM's response as a string
        """
        messages = [SystemMessage(content=system_prompt)]

        # Add chat history if provided
        if chat_history:
            for message in chat_history:
                if message["role"] == "user":
                    messages.append(HumanMessage(content=message["content"]))
                elif message["role"] == "assistant":
                    messages.append(AIMessage(content=message["content"]))

        # Add the current user input
        messages.append(HumanMessage(content=user_input))

        # Generate response
        response = self.llm.invoke(messages)

        return response.content
