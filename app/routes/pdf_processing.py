import time
print(f"[{time.time()}] Starting import of PDF Processing import")
from typing import Optional
import os, uuid, boto3

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vector_store import upsert_text_chunks 
from app.models.pdf_model import PDFUploadResponse

router = APIRouter()

# Initialize S3 client and bucket
s3 = boto3.client("s3")
BUCKET = os.environ["PDF_UPLOAD_BUCKET"]

def extract_text_from_pdf(file_path):
    """Extracts text from a given PDF file"""
    print("extract_text_from_pdf execution started")
    from PyPDF2 import PdfReader
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

@router.post(
    "/upload/",
    response_model=PDFUploadResponse,
    summary="Upload a PDF and index its text",
)
async def upload_pdf(file: UploadFile = File(...), chat_id: Optional[str] = None):
    """
        1. If no chat_id provided, generate a new one.
        2. Write the file to /tmp, upload it to S3.
        3. Extract text, chunk it, upsert to Pinecone.
        4. Return chat_id in response.
    """
    # Lazy‑load PyPDF2 and Langchain only when needed
    from langchain.text_splitter import CharacterTextSplitter

    print("upload_pdf started...")

    # Step 1: Generate chat_id if not provided
    if not chat_id:
        chat_id = str(uuid.uuid4())
    
    # Step 2: Write to Lambda temp space
    # file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # with open(file_path, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as buffer:
        buffer.write(await file.read())

    # Upload the raw PDF to S3 for persistence
    
    s3.upload_file(tmp_path, BUCKET, f"{chat_id}/{file.filename}")

    
    # Step 3: Extract text from PDF
    raw_text = extract_text_from_pdf(tmp_path)
    
    # Step 4: Split text into chunks
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    text_chunks = text_splitter.split_text(raw_text)
    print(f"📝 Split into {len(text_chunks)} chunks; first chunk preview:\n{text_chunks[0][:200]}")

    
    if not text_chunks:
        print("An exception occured while uploading...")
        raise HTTPException(status_code=400, detail="PDF contains no extractable text.")
    
    # Step 5: Upsert chunks into Pinecone under this chat_id
    upsert_text_chunks(text_chunks, chat_id)

    print("upload_pdf method executed successfully!!", "num_chunks:", len(text_chunks))

    return PDFUploadResponse(
        message="File processed successfully",
        num_chunks=len(text_chunks),
        chat_id=chat_id
    )
