from typing import *
from fastapi import APIRouter, HTTPException, Request
from app.models.chat_model import ChatRequest
from app.services.vector_store import query_text_chunks
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import app.state

router = APIRouter()

# For demonstration, store chat histories in a dictionary, keyed by chat_id
chat_histories: Dict[str, List] = {}

@router.post("/ask/")
async def ask_question(payload: ChatRequest):
    """
        Takes a chat_id and question, retrieves relevant PDF text from Pinecone,
        and uses LLM to generate an answer.
    """
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
    print("📥 Received docs")

    # Format them into a single string for context
    context = "\n\n".join(doc.page_content for doc in docs)

    # 2. Check chat history for this session
    print("checking if chat_id is present in chat_histories")
    if chat_id not in chat_histories:
        print("chat_id:", chat_id, "not found in chat_histories")
        print("Adding the new chat_id to chat_histories")
        chat_histories[chat_id] = []

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

    # 4. Create an LLM instance
    print("creating llm instance....")
    llm = ChatOpenAI()

    # 5. Build a chain in a pipeline style (depending on your LangChain version)
    print("🔄 Creating chain...")
    chain = (
        {
            "context": lambda x: context,
            "chat_history": lambda x: chat_histories[chat_id],
            "question": lambda x: question
        } | prompt | llm
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
    chat_histories[chat_id].append(HumanMessage(content=question))
    chat_histories[chat_id].append(AIMessage(content=answer))

    print("✅ ask_questions method successfully executed")

    return {"response": answer}
