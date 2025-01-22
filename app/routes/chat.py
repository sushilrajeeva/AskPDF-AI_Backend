from fastapi import APIRouter, HTTPException, Request
from app.models.chat_model import ChatRequest
from app.services.vector_store import get_vectorstore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import app.state

router = APIRouter()
chat_history = []

@router.post("/ask/")
async def ask_question(request: Request):
    """Handles user questions and retrieves AI-generated responses"""

    print("✅ Entered ask_questions method")

    # ✅ Check if vector store exists
    if app.state.vector_store is None:
        print("❌ Error: App State is None")
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload a PDF first.")

    vector_store = app.state.vector_store
    retriever = vector_store.as_retriever()

    request_json = await request.json()
    print("📥 Received request:", request_json)

    if "question" not in request_json or not request_json["question"]:
        print("❌ Missing question field in request")
        raise HTTPException(status_code=400, detail="Missing required field: 'question'")

    llm = ChatOpenAI()

    system_template = """You are a helpful AI assistant. Use the following pieces of context to answer the human's question. If you don't know the answer, say that you don't know.

    Context: {context}"""

    print("📝 Creating Prompt...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])

    print("✅ Prompt created.")

    def format_docs(docs):
        print(f"📄 Format Docs started... {len(docs)} documents found")
        return "\n\n".join(doc.page_content for doc in docs)

    print("🔄 Creating chain...")
    
    # ✅ Correctly format the chain
    chain = (
        {
            "context": lambda x: format_docs(retriever.get_relevant_documents(x["question"])),
            "chat_history": lambda x: chat_history,
            "question": lambda x: x["question"]
        }
        | prompt  # ✅ Ensure prompt is part of the pipeline
        | llm  # ✅ Pass data correctly to the LLM
    )

    try:
        print("🚀 Executing chain.invoke()...")
        response = chain.invoke({"question": request_json["question"]})
        print("✅ Chain executed. Raw Response:", response)

        # ✅ Extract only the response text
        if isinstance(response, dict) and "content" in response:
            response_text = response["content"]
        elif hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)  # Convert to string as fallback

        print("✅ Extracted response:", response_text)

    except Exception as e:
        print("❌ Error in LangChain pipeline:", str(e))
        raise HTTPException(status_code=500, detail="Internal error in AI processing.")

    chat_history.append(HumanMessage(content=request_json["question"]))
    chat_history.append(AIMessage(content=response_text))  # ✅ Fix: Use extracted text

    print("✅ ask_questions method successfully executed")
    return {"response": response_text}
