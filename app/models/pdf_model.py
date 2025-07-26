from pydantic import BaseModel

class PDFUploadResponse(BaseModel):
    message: str
    num_chunks: int
    chat_id: str

