import time
print(f"[{time.time()}] Starting import of fastapi…")
from fastapi import FastAPI
print(f"[{time.time()}] fastapi imported, now mangum…")
from fastapi.middleware.cors import CORSMiddleware
from app.routes import pdf_processing, chat
from app.config import load_env

print(f"[{time.time()}] mangum imported, now other modules…")
from mangum import Mangum
import os

# Load environment variables
load_env()

# Initialize FastAPI with "/api" prefix
app = FastAPI(title="PDF Chat API", description="Chat with multiple PDFs using AI", root_path="/api")

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

@app.get("/health", include_in_schema=False)
def health_check():
    return {
      "status": "ok",
      "bucket": os.environ.get("PDF_UPLOAD_BUCKET", "<missing>")
    }

handler = Mangum(app)