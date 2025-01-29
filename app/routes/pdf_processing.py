from typing import *

from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from app.services.vector_store import upsert_text_chunks 
from app.models.pdf_model import PDFUploadResponse
import app.state  # ✅ Import global state

import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_pdf(file_path):
    """Extracts text from a given PDF file"""
    print("extract_text_from_pdf execution started")
    text = ""
    pdf_reader = PdfReader(file_path)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    if not text.strip():
        raise HTTPException(status_code=400, detail="PDF contains no extractable text.")
    
    print("extract_text_from_pdf executed successfully")
    return text

@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...), chat_id: Optional[str] = None):
    """
        1. If no chat_id provided, generate a new one.
        2. Save the PDF, extract text, chunk it, and upsert to Pinecone with chat_id as metadata.
        3. Return chat_id in response.
    """

    print("upload_pdf started...")

    # Step 1: Generate chat_id if not provided
    if not chat_id:
        chat_id = str(uuid.uuid4())
    
    # Step 2: Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Step 3: Extract text from PDF
    raw_text = extract_text_from_pdf(file_path)
    
    # Step 4: Split text into chunks
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    text_chunks = text_splitter.split_text(raw_text)
    
    if not text_chunks:
        print("An exception occured while uploading...")
        raise HTTPException(status_code=400, detail="PDF contains no extractable text.")
    
    # Step 5: Upsert chunks into Pinecone under this chat_id
    upsert_text_chunks(text_chunks, chat_id)

    print("upload_pdf method executed successfully!!", "num_chunks:", len(text_chunks))

    return {
        "message": "File processed successfully",
        "num_chunks": len(text_chunks),
        "chat_id": chat_id
    }
