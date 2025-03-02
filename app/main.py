from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import uvicorn

from app.api.routes import router as api_router
from app.config import BASE_DIR, OPENAI_API_KEY

# Initialize FastAPI app
app = FastAPI(
    title="Cocktail Advisor Chat",
    description="A chat application for cocktail recommendations and information",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=Path(BASE_DIR) / "static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=Path(BASE_DIR) / "templates")

# Include API routes
app.include_router(api_router, prefix="/api", tags=["api"])

# Check if OpenAI API key is set
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY is not set. The application may not function correctly.")

# Root route - Serve the chat interface
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An error occurred: {str(exc)}"}
    )

# Main entry point
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
