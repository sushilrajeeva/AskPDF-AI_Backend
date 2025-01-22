from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from app.services.vector_store import get_vectorstore
from app.models.pdf_model import PDFUploadResponse
import app.state  # ✅ Import global state

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF file"""
    print("extract_text_from_pdf execution started")
    text = ""
    pdf_reader = PdfReader(pdf_path)
    for page in pdf_reader.pages:
        text += page.extract_text()
    print("extract_text_from_pdf executed successfully")
    return text

@router.post("/upload/", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Handles PDF file uploads and text extraction"""

    print("upload_pdf started...")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract text from PDF
    raw_text = extract_text_from_pdf(file_path)
    
    # Split into chunks
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    text_chunks = text_splitter.split_text(raw_text)
    
    if not text_chunks:
        print("An exception occured while uploading...")
        raise HTTPException(status_code=400, detail="PDF contains no extractable text.")
    
    # ✅ Store vector store in global state
    app.state.vector_store = get_vectorstore(text_chunks)

    print("upload_pdf method executed successfully!!")

    return {"message": "File processed successfully", "num_chunks": len(text_chunks)}
