# import os
# from dotenv import load_dotenv

# def load_env():
#     """Loads environment variables from .env file"""
#     load_dotenv()

import os

def load_env():
    """
    Locally: loads from .env
    In Lambda: AWS injects env vars, so do nothing.
    """
    if os.getenv("AWS_EXECUTION_ENV") is None:
        # only load .env when NOT running in Lambda
        from dotenv import load_dotenv
        load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
PDF_UPLOAD_BUCKET = os.getenv("PDF_UPLOAD_BUCKET")  # name of the S3 bucket
