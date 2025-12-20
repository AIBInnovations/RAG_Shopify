import uuid
from typing import Dict, Any, Optional

class SessionManager:
    def __init__(self):
        # {session_id: {'brand_id': str, 'history': [], 'attributes': {}, 'last_product': str}}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, brand_id: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "brand_id": brand_id,
            "history": [], 
            "last_product_context": None,
            "user_attributes": {} # New: Stores 'skin_type', 'concern', etc.
        }
        return session_id

    def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    def get_context_handle(self, session_id: str) -> Optional[str]:
        session = self.sessions.get(session_id)
        return session.get("last_product_context") if session else None

    def add_interaction(self, session_id: str, role: str, message: str):
        if session_id in self.sessions:
            self.sessions[session_id]["history"].append({"role": role, "content": message})
            # Keep history optimized (Last 10 turns)
            if len(self.sessions[session_id]["history"]) > 10:
                self.sessions[session_id]["history"].pop(0)

    def update_context(self, session_id: str, product_handle: str):
        if session_id in self.sessions:
            self.sessions[session_id]["last_product_context"] = product_handle

    def update_user_attribute(self, session_id: str, key: str, value: str):
        """Remembers things like 'dry skin' or 'hair fall'."""
        if session_id in self.sessions:
            self.sessions[session_id]["user_attributes"][key] = value