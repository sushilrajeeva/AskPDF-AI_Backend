from langchain_community.vectorstores import FAISS
from app.services.embeddings import get_openai_embeddings, get_huggingface_embeddings

def get_vectorstore(text_chunks, use_openai=True):
    """Creates a FAISS vector store from text chunks"""
    embeddings = get_openai_embeddings() if use_openai else get_huggingface_embeddings()
    return FAISS.from_texts(texts=text_chunks, embedding=embeddings)
