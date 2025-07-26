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
    embeddings      = get_openai_embeddings() if use_openai else get_huggingface_embeddings()

    namespace       = "askpdf-namespace"  # you can rename or make it configurable
    metadata_list   = [{"chat_id": chat_id} for _ in text_chunks]
    get_pinecone_index()

    # This automatically upserts into Pinecone
    PineconeVectorStore.from_texts(
        texts       = text_chunks,
        embedding   = embeddings,
        index_name  = PINECONE_INDEX_NAME,
        namespace   = namespace,
        metadatas   = metadata_list,
        async_req   = False,      # run synchronously
        pool_threads= 1        # effectively no pool
    )


def query_text_chunks(question: str, chat_id: str, top_k: int = 3, use_openai: bool = True):
    """
    1. Embed the user question using OpenAI or HuggingFace.
    2. Query Pinecone, filtering by metadata {"chat_id": chat_id} so we only get that chat's docs.
    3. Return a list of LangChain 'Document' objects.
    """

    embeddings      = get_openai_embeddings() if use_openai else get_huggingface_embeddings()
    index           = get_pinecone_index()
    namespace       = "askpdf-namespace"

    print("This is the index:", index)
    print("this is the index name:", PINECONE_INDEX_NAME)

    # Create a Pinecone VectorStore from the existing index
    vectorstore = PineconeVectorStore(
        index       = index,
        embedding   = embeddings,
        text_key    = "text",       # If you want doc.page_content to come from metadata["text"]
        namespace   = namespace
    )

    # Apply a filter so we only search vectors belonging to this chat
    docs_no_filter = vectorstore.similarity_search(
        query   = question,
        k       = top_k,
    )

    print("without filter :", docs_no_filter)

    docs = vectorstore.similarity_search(
        query   = question,
        k       = top_k,
        filter  = {"chat_id": chat_id}
    )
    print(f"Retrieved {len(docs)} docs for chat_id={chat_id}")
    for doc in docs:
        print("→", doc.page_content[:200])

    return docs
