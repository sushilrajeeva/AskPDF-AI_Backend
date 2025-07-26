

from app.config import OPENAI_API_KEY, HUGGINGFACEHUB_API_TOKEN

def get_openai_embeddings():
    """Returns OpenAI embeddings"""
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def get_huggingface_embeddings():
    """Returns HuggingFace embeddings"""
    from langchain_community.embeddings import HuggingFaceInstructEmbeddings
    return HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl", api_key=HUGGINGFACEHUB_API_TOKEN)
