# Cocktail Advisor Chat

A Python-based chat application that integrates with a large language model (LLM) to create a Retrieval-Augmented Generation (RAG) system using a vector database for cocktail recommendations and information.

## Overview

This project implements a cocktail recommendation system that:
- Answers questions about cocktails and ingredients
- Remembers user preferences (favorite ingredients/cocktails)
- Provides personalized cocktail recommendations
- Uses RAG to enhance LLM responses with cocktail knowledge

## Features

- **Knowledge Base** - Answers questions about cocktails, ingredients, and recipes
- **User Memory** - Remembers preferences and favorites
- **Personalized Recommendations** - Based on user preferences and similarity
- **RAG Implementation** - Enhances LLM responses with cocktail data
- **Chat Interface** - Simple and intuitive user interface

## Tech Stack

- **Backend**: FastAPI, Python
- **NLP**: LangChain, OpenAI GPT
- **Vector Database**: FAISS
- **Embeddings**: Sentence Transformers
- **Frontend**: HTML, CSS, JavaScript (vanilla)

## Running the Project Locally

### Prerequisites

- Python 3.9+
- OpenAI API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cocktail-advisor-chat.git
   cd cocktail-advisor-chat
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a `.env` file in the project root with your OpenAI API key**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

6. **Run the application**
   ```bash
   # Navigate to the project root directory if you're not already there
   cd cocktail-advisor-chat
   
   # Start the FastAPI server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   You should see output similar to:
   ```
   INFO:     Started server process [xxxx]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

7. **Access the application**
   - Open your web browser and navigate to:
     ```
     http://localhost:8000
     ```
   - You should see the Cocktail Advisor Chat interface
   - You can also access the API documentation at:
     ```
     http://localhost:8000/docs
     ```

### Testing the Application

You can test the application with the following example queries:

#### Knowledge Base Queries
- "What are the 5 cocktails containing lemon?"
- "What are the 5 non-alcoholic cocktails containing sugar?"
- "What are my favourite ingredients?"

#### Advisor Queries
- "Recommend 5 cocktails that contain my favourite ingredients"
- "Recommend a cocktail similar to 'Hot Creamy Bush'"
- "I really like rum and pineapple juice. What can you recommend?"

## Project Structure

```
cocktail_advisor/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py             # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm.py                # LLM integration
│   │   ├── vectordb.py           # Vector database operations
│   │   ├── rag.py                # RAG implementation
│   │   ├── memory.py             # User memory management
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_processor.py     # Data processing utilities
│   │   ├── prompt_templates.py   # LLM prompt templates
├── data/
│   ├── cocktails.csv             # Pre-loaded dataset of cocktails
├── static/
│   ├── css/
│   │   ├── style.css             # CSS styles
│   ├── js/
│   │   ├── chat.js               # JavaScript for chat interface
├── templates/
│   ├── index.html                # Chat interface
├── scripts/                       # Utility scripts (if needed)
├── requirements.txt              # Project dependencies
├── README.md                     # Project documentation
```

## Summary of Results and Implementation Approach

### Results

The Cocktail Advisor Chat successfully implements all the required functionality:

1. **Knowledge Base**:
   - Accurately retrieves cocktails based on ingredients (e.g., lemon, sugar)
   - Differentiates between alcoholic and non-alcoholic cocktails
   - Provides detailed information about cocktail recipes and preparation

2. **User Memory**:
   - Detects and stores user preferences from natural language
   - Remembers favorite ingredients and cocktails across sessions
   - Provides preference information when asked

3. **Recommendations**:
   - Generates personalized recommendations based on favorite ingredients
   - Finds similar cocktails based on ingredient composition
   - Provides relevant suggestions with explanations

4. **RAG Integration**:
   - Successfully enhances LLM responses with cocktail knowledge
   - Provides accurate, context-aware answers to cocktail queries
   - Maintains a natural, conversational experience

### Implementation Approach and Thought Process

#### 1. Modular Design
I chose a modular architecture to separate concerns and make the code maintainable:
- Data processing is isolated from vector operations
- User memory management is independent from the RAG system
- The API layer is decoupled from the core functionality

#### 2. RAG Implementation Strategy
For the RAG system, I implemented a query-type detection approach to:
- Identify the intent behind user queries (ingredient query, cocktail query, recommendation, etc.)
- Route queries to specialized handlers
- Retrieve only the most relevant information for each query type
- Structure the context to optimize the LLM's understanding

#### 3. Vector Database Choices
I used FAISS for the vector database because:
- It's lightweight and works well for local development
- It provides efficient similarity search
- It doesn't require external services, simplifying deployment

#### 4. User Preference Detection
For detecting user preferences, I implemented:
- Pattern matching with regular expressions to identify expressions of preference
- Context-aware storage to distinguish between ingredients and cocktails
- A memory system that persists across sessions

#### 5. Frontend Considerations
The frontend was designed to be:
- Lightweight (vanilla JavaScript, no heavy frameworks)
- Responsive (works on different screen sizes)
- Intuitive (clear interface with example questions)
- Informative (displays user preferences for transparency)

#### 6. Challenges and Solutions

**Challenge**: Extracting structured ingredient data from unstructured text descriptions.
**Solution**: Implemented robust regex patterns and cleaning functions to handle variations in ingredient formatting.

**Challenge**: Distinguishing between similar query types (e.g., asking about a cocktail vs. asking for recommendations).
**Solution**: Created a hierarchical query classifier with specialized patterns for different query types.

**Challenge**: Making the LLM responses grounded in factual cocktail information.
**Solution**: Carefully structured the RAG context to emphasize relevant cocktail data and used specific system prompts.

## Future Improvements

- Implement a more sophisticated NLP approach for preference detection
- Add multi-user support with authentication
- Enhance the vector search with hybrid retrieval (combining keyword and semantic search)
- Add visualization of cocktail data (images, ingredient proportions)
- Implement caching for improved performance
- Add a mobile app interface

## Conclusion

This Cocktail Advisor Chat demonstrates how RAG systems can be applied to create domain-specific assistants that combine the flexibility of LLMs with the factual accuracy of structured data. The system successfully leverages vector search to retrieve relevant cocktail information and enhances LLM responses with this domain knowledge, creating a helpful, personalized cocktail recommendation experience.