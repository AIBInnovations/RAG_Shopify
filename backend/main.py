from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv() 

from .models import ChatRequest, ChatResponse, SessionStartRequest
from .data_engine import MultiTenantDataEngine
from .session_manager import SessionManager
from .llm_gateway import LLMGateway

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_engine = MultiTenantDataEngine()
session_manager = SessionManager()
llm_gateway = LLMGateway()

@app.post("/start_session")
async def start_session(request: SessionStartRequest):
    if request.brand_id not in data_engine.brand_metadata:
        raise HTTPException(status_code=400, detail="Invalid Brand ID")
    session_id = session_manager.create_session(request.brand_id)
    return {"session_id": session_id, "message": f"Welcome to {request.brand_id.capitalize()} support!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session expired or invalid")

    brand_id = session['brand_id']
    query = request.message

    # 1. RETRIEVE CONTEXT
    last_handle = session_manager.get_context_handle(request.session_id)
    
    # 2. RETRIEVE SHOP INFO (New!)
    shop_info = data_engine.get_shop_details(brand_id)

    # 3. SMART SEARCH
    relevant_products = data_engine.search_products(brand_id, query, last_handle)

    if relevant_products and relevant_products[0].match_quality == "direct":
        session_manager.update_context(request.session_id, relevant_products[0].handle)

    # 4. LLM Generation (Pass shop_info now)
    response_text = llm_gateway.generate_response(
        query=query,
        context_products=relevant_products,
        history=session['history'],
        brand_name=brand_id.capitalize(),
        shop_info=shop_info # <--- PASS THIS
    )

    session_manager.add_interaction(request.session_id, "user", query)
    session_manager.add_interaction(request.session_id, "assistant", response_text)

    return ChatResponse(
        response=response_text,
        related_products=[p.dict() for p in relevant_products]
    )
