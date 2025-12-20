from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SessionStartRequest(BaseModel):
    brand_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    related_products: List[Dict[str, Any]] = []

class ProductVariant(BaseModel):
    id: str
    title: str
    price: str
    inventory_qty: int
    inventory_policy: str
    sku: str

class ProductContext(BaseModel):
    handle: str
    title: str
    description: str
    tags: List[str]
    vendor: str
    variants: List[ProductVariant]
    url: str
    price_range: str = "Not specified"
    ingredients: str = "Not specified"
    # New Field: Tells LLM if this is a real result or a fallback
    match_quality: str = "direct"  # Values: "direct", "synonym", "fallback"