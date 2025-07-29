import time
from typing import List, Dict
from fastapi import APIRouter, HTTPException

print(f"[{time.time()}] Starting import of chat.py")
from app.models.chat_model import ChatRequest
import os, boto3
from botocore.exceptions import ClientError

import app.state

router = APIRouter()

# DynamoDB setup
dynamodb = boto3.resource("dynamodb")
history_table = dynamodb.Table(os.environ["CHAT_HISTORY_TABLE"])


@router.post("/ask/")
async def ask_question(payload: ChatRequest):
    """
    Takes a chat_id and question, retrieves relevant PDF text from Pinecone,
    and uses LLM to generate an answer.
    """
    # Lazy‑load LangChain & LLMs only when needed
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    from langchain_core.output_parsers import StrOutputParser
    from app.services.vector_store import query_text_chunks
    
    chat_id = payload.chat_id
    question = payload.question

    print(f"[ask_questions] Processing question for chat_id={chat_id}")

    if not chat_id:
        raise HTTPException(status_code=400, detail="No chat_id provided. Please upload a PDF first.")

    if not question.strip():
        raise HTTPException(status_code=400, detail="No question provided.")

    # 1. Retrieve relevant documents from Pinecone
    print(f"[ask_questions] Querying Pinecone for chat_id={chat_id}")
    try:
        docs = query_text_chunks(question, chat_id, top_k=4)
    except Exception as e:
        print(f"[ask_questions] Error querying Pinecone: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")
    
    if not docs:
        print(f"[ask_questions] No documents found for chat_id={chat_id}")
        raise HTTPException(
            status_code=404, 
            detail=f"No documents found for chat_id={chat_id}. Please ensure you've uploaded a PDF with this chat_id."
        )
    
    print(f"[ask_questions] Retrieved {len(docs)} chunks")
    
    # Format them into a single string for context
    context = "\n\n".join(doc.page_content for doc in docs)
    print(f"[ask_questions] Context length: {len(context)} characters")

    # 2. Load prior history from DynamoDB
    try:
        resp = history_table.get_item(Key={"chat_id": chat_id})
        messages = resp.get("Item", {}).get("messages", [])
    except ClientError as e:
        print(f"[ask_questions] Error loading chat history: {str(e)}")
        messages = []

    # Reconstruct Langchain messages
    chat_history = []
    for i, m in enumerate(messages):
        chat_history.append(
            HumanMessage(content=m) if i % 2 == 0 else AIMessage(content=m)
        )

    # 3. Build the prompt
    print("[ask_questions] Building prompt...")
    system_template = """You are a helpful AI assistant. Use the following context to answer the user's question.
    If the context doesn't contain relevant information to answer the question, say so.
    
    Context: {context}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])

    # 4. Create an LLM instance
    print("[ask_questions] Creating LLM instance...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 5. Build a chain
    print("[ask_questions] Creating chain...")
    chain = prompt | llm | StrOutputParser()

    try:
        print("[ask_questions] Invoking chain...")
        response = chain.invoke({
            "context": context,
            "chat_history": chat_history,
            "question": question
        })
        print(f"[ask_questions] Chain executed successfully")
    except Exception as e:
        print(f"[ask_questions] Error executing chain: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

    # Extract the answer text
    answer = str(response)
    print(f"[ask_questions] Generated answer: {answer[:200]}...")

    # 6. Update chat history
    try:
        messages.extend([question, answer])
        history_table.put_item(Item={"chat_id": chat_id, "messages": messages})
        print(f"[ask_questions] Updated chat history")
    except Exception as e:
        print(f"[ask_questions] Error updating chat history: {str(e)}")
        # Don't fail the request if history update fails

    return {"response": answer}