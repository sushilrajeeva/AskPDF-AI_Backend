# app/services/vector_store.py

from typing import List
# from langchain_community.vectorstores import Pinecone
from langchain_pinecone import PineconeVectorStore
from app.services.embeddings import get_openai_embeddings, get_huggingface_embeddings
from app.services.pinecone_setup import get_pinecone_index, PINECONE_INDEX_NAME

def upsert_text_chunks(text_chunks: List[str], chat_id: str, use_openai: bool = True):
    """
    1. Embeds the text_chunks (either OpenAI or HuggingFace).
    2. Upserts them into Pinecone under a single namespace (e.g. "askpdf-namespace")
       with metadata={"chat_id": chat_id}.
    """
    # Choose which embeddings to use
    embeddings = get_openai_embeddings() if use_openai else get_huggingface_embeddings()
    
    namespace = "askpdf-namespace"  # you can rename or make it configurable
    metadata_list = [{"chat_id": chat_id} for _ in text_chunks]
    
    # Get the index with pool_threads=1 for Lambda compatibility
    index = get_pinecone_index()
    
    # Create vectorstore with proper configuration for Lambda
    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
        namespace=namespace
    )
    
    # Add texts with Lambda-compatible settings
    vectorstore.add_texts(
        texts=text_chunks,
        metadatas=metadata_list,
        namespace=namespace,
        batch_size=32,
        embedding_chunk_size=1000,
        async_req=False,  # CRITICAL: Set to False for Lambda
    )
    
    print(f"Successfully upserted {len(text_chunks)} chunks for chat_id={chat_id}")

def query_text_chunks(question: str, chat_id: str, top_k: int = 3, use_openai: bool = True):
    """
    1. Embed the user question using OpenAI or HuggingFace.
    2. Query Pinecone, filtering by metadata {"chat_id": chat_id} so we only get that chat's docs.
    3. Return a list of LangChain 'Document' objects.
    """
    embeddings = get_openai_embeddings() if use_openai else get_huggingface_embeddings()
    index = get_pinecone_index()
    namespace = "askpdf-namespace"
    
    print(f"Querying for chat_id={chat_id} in namespace={namespace}")
    
    # Create a Pinecone VectorStore from the existing index
    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
        namespace=namespace
    )
    
    # Debug: First try without filter to verify data exists
    docs_no_filter = vectorstore.similarity_search(
        query=question,
        k=top_k,
        namespace=namespace
    )
    print(f"Debug - Documents found without filter: {len(docs_no_filter)}")
    
    # Now apply the filter
    filter_dict = {"chat_id": {"$eq": chat_id}}  # Use proper Pinecone filter syntax
    
    docs = vectorstore.similarity_search(
        query=question,
        k=top_k,
        filter=filter_dict,
        namespace=namespace
    )
    
    print(f"Retrieved {len(docs)} docs for chat_id={chat_id}")
    for i, doc in enumerate(docs):
        print(f"→ Doc {i}: {doc.page_content[:200]}...")
        print(f"  Metadata: {doc.metadata}")
    
    return docs