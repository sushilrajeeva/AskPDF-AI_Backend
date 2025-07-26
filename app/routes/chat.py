import time
from typing import List, Dict
from fastapi import APIRouter, HTTPException

print(f"[{time.time()}] Starting import of chat.py")
from app.models.chat_model import ChatRequest
import os, boto3
from botocore.exceptions import ClientError


import app.state

router = APIRouter()

# For demonstration, store chat histories in a dictionary, keyed by chat_id
# chat_histories: Dict[str, List] = {}
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

    print("Entered ask_questions method")

    if not chat_id:
        raise HTTPException(status_code=400, detail="No chat_id provided. Please upload a PDF first.")

    if not question.strip():
        raise HTTPException(status_code=400, detail="No question provided.")

    # 1. Retrieve relevant documents from Pinecone
    print("Querying text chunks to retrieve documents from Pinecone")
    docs = query_text_chunks(question, chat_id, top_k=4)
    print(f"Retrieved {len(docs)} chunks for chat_id={chat_id}")
    for i, doc in enumerate(docs):
        print(f" → Doc {i} preview: {doc.page_content[:200]}")

    # Format them into a single string for context
    context = "\n\n".join(doc.page_content for doc in docs)

    # # 2. Check chat history for this session
    # print("checking if chat_id is present in chat_histories")
    # if chat_id not in chat_histories:
    #     print("chat_id:", chat_id, "not found in chat_histories")
    #     print("Adding the new chat_id to chat_histories")
    #     chat_histories[chat_id] = []

    # 2. Load prior history from DynamoDB
    try:
        resp = history_table.get_item(Key={"chat_id": chat_id})
        messages = resp.get("Item", {}).get("messages", [])
    except ClientError:
        messages = []

    # Reconstruct Langchain messages
    chat_history = []
    for i, m in enumerate(messages):
        chat_history.append(
            HumanMessage(content=m) if i % 2 == 0 else AIMessage(content=m)
        )

    # 3. Build the prompt
    print("building prompt...")
    system_template = """You are a helpful AI assistant. Use the following context to answer:
    If you're unsure, say "I don't know."

    Context: {context}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])

    print("Prompt created.")

    # 4. Create an LLM instance, pinned to gpt-4o-mini
    print("creating llm instance with gpt-4o-mini....")
    llm = ChatOpenAI(model="gpt-4o-mini")

    # 5. Build a chain in a pipeline style (depending on your LangChain version)
    print("🔄 Creating chain...")
    chain = (
        {
            "context": lambda x: context,
            "chat_history": lambda x: chat_history,
            "question": lambda x: question
        } | prompt | llm | StrOutputParser()  # ensures we get raw text, not additional metadata
    )

    try:
        print("🚀 Executing chain.invoke()...")
        response = chain.invoke({})
        print("✅ Chain executed. Raw Response:", response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Extract the answer text
    if isinstance(response, dict) and "content" in response:
        answer = response["content"]
    else:
        answer = str(response)

    print("✅ Extracted response:", answer)

    # 6. Update chat history
    # Append and persist back to DynamoDB
    messages.extend([question, answer])
    history_table.put_item(Item={"chat_id": chat_id, "messages": messages})
    # chat_histories[chat_id].append(HumanMessage(content=question))
    # chat_histories[chat_id].append(AIMessage(content=answer))

    print("✅ ask_questions method successfully executed")

    return {"response": answer}
