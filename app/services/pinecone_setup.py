import os

# if running locally, load .env once
if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()

from pinecone import Pinecone, ServerlessSpec

# read your Pinecone config exactly once
PINECONE_API_KEY    = os.getenv("PINECONE_API_KEY")       # e.g. pcsk_xxx
PINECONE_ENV        = os.getenv("PINECONE_ENV")           # e.g. us‑east‑1‑aws
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")    # e.g. askpdf‑index

# 1. Create a Pinecone client instance
pc = Pinecone(api_key=PINECONE_API_KEY)

# 2. Optionally: check if our index already exists, create if it doesn't.
#    If you already created your index in the Pinecone console, you can skip this step.
indexes = pc.list_indexes().names()  # Get existing index names
if not pc.has_index(PINECONE_INDEX_NAME):
    # Example only if you want to create the index from code:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,    # match your embedding dimension
        metric="cosine",   # or "dotproduct"/"euclidean"
        spec=ServerlessSpec(
            cloud="aws",
            region=PINECONE_ENV
        )
    )

def get_pinecone_index():
    return pc.Index(PINECONE_INDEX_NAME)

