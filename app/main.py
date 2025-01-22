from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import pdf_processing, chat
from app.config import load_env

# Load environment variables
load_env()

# Initialize FastAPI with "/api" prefix
app = FastAPI(title="PDF Chat API", description="Chat with multiple PDFs using AI", openapi_prefix="/api")

# ✅ Fix CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (You can change this in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes (Now prefixed with "/api")
app.include_router(pdf_processing.router, prefix="/pdf", tags=["PDF Processing"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

@app.get("/")
def home():
    return {"message": "Welcome to AskPDF-AI Chat API!"}