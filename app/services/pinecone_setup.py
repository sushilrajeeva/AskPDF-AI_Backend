import os

# if running locally, load .env once
if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()

from pinecone import Pinecone, ServerlessSpec

# read your Pinecone config exactly once
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")       # e.g. pcsk_xxx
PINECONE_ENV = os.getenv("PINECONE_ENV")              # e.g. us‑east‑1
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME") # e.g. askpdf‑index

# 1. Create a Pinecone client instance
pc = Pinecone(api_key=PINECONE_API_KEY)

# 2. Check if our index already exists, create if it doesn't
if not pc.has_index(PINECONE_INDEX_NAME):
    # Create index with proper configuration
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,    # OpenAI text-embedding-3-small dimension
        metric="cosine",   # or "dotproduct"/"euclidean"
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENV
        )
    )
    print(f"Created new Pinecone index: {PINECONE_INDEX_NAME}")
else:
    print(f"Using existing Pinecone index: {PINECONE_INDEX_NAME}")

def get_pinecone_index():
    """
    Returns a Pinecone Index instance with pool_threads=1 for Lambda compatibility
    """
    # For Lambda, use pool_threads=1 to avoid threading issues
    return pc.Index(PINECONE_INDEX_NAME, pool_threads=1)