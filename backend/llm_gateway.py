import os
import traceback
from groq import Groq, RateLimitError, APIError
from typing import List, Dict, Any
from .models import ProductContext
from .business_rules import BusinessRules


class LLMGateway:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ CRITICAL: GROQ_API_KEY missing.")
        self.client = Groq(api_key=api_key)

        self.model_cascade = [
            "llama-3.3-70b-versatile",
            "deepseek-r1-distill-llama-70b",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant"
        ]

    def generate_response(
        self,
        query: str,
        context_products: List[ProductContext],
        history: List[Dict],
        brand_name: str,
        shop_info: Dict[str, Any]
    ) -> str:

        # 1. Sort Products
        sorted_products = BusinessRules.sort_products_for_context(
            context_products, query
        )

        # 2. Match Quality & Search Status
        match_type = "none"
        search_status = "NO_PRODUCTS_FOUND"

        if sorted_products:
            match_type = sorted_products[0].match_quality  # direct / catalog / fallback

            if match_type == "direct":
                search_status = "DIRECT_MATCH"
            elif match_type == "catalog":
                search_status = "CATALOG_REQUEST"
            elif match_type == "fallback":
                search_status = "NO_DIRECT_MATCH (Fallback Items)"

        # 3. PRODUCT DATA Block
        product_text = ""
        if not sorted_products:
            product_text = "NO MATCHING PRODUCTS FOUND IN CATALOG."
        else:
            for p in sorted_products:
                stock_status = BusinessRules.get_stock_status(p.variants)
                sale_tag = "🔥 ON SALE" if "ON SALE" in p.price_range else ""
                tags_str = ", ".join(p.tags[:5])

                product_text += f"""
---
PRODUCT: {p.title}
URL: {p.url}
PRICE: {p.price_range} {sale_tag}
STOCK: {stock_status}
TAGS: {tags_str}
DETAILS: {p.description[:700]}
---
"""

        # 4. Intent Instruction
        if match_type == "catalog":
            state_instruction = (
                "USER INTENT: Browsing the catalog.\n"
                "ACTION: Recommend products enthusiastically."
            )
        elif match_type == "fallback":
            state_instruction = (
                f"USER INTENT: Search failed for '{query}'.\n"
                "ACTION: Apologize briefly and suggest popular alternatives."
            )
        elif match_type == "direct":
            state_instruction = (
                "USER INTENT: Specific product inquiry.\n"
                "ACTION: Answer strictly using PRODUCT DATA."
            )
        else:
            state_instruction = (
                "USER INTENT: No product intent detected.\n"
                "ACTION: Respond naturally without forcing products."
            )

        # 5. Off-topic / Competitor Guard
        off_topic_instruction = ""
        if BusinessRules.is_off_topic_query(query):
            off_topic_instruction = f"""
🚨 OFF-TOPIC QUERY DETECTED
ACTION: Politely refuse.

RESPONSE TEMPLATE:
"I am the AI assistant for {brand_name} only.
I cannot provide information about other brands, platforms, or unrelated topics."
"""

        # 6. Shop Context
        shop_context = f"""
BRAND DETAILS:
- Support Email: {shop_info.get('email', 'Check website')}
- Phone: {shop_info.get('phone', 'Not listed')}
- Domain: {shop_info.get('domain', '')}
- Currency: {shop_info.get('currency', 'INR')}
"""

        # 7. SYSTEM PROMPT (Unified Intelligence + Safety)
        system_prompt = f"""
You are the official AI Product Assistant for the brand '{brand_name}'.

🔴 NON-NEGOTIABLE RULES:
1. BRAND ISOLATION: You ONLY know '{brand_name}'. Never mention competitors.
2. SOURCE OF TRUTH: Use PRODUCT DATA only. If missing, say "I don't have that information."
3. NO HALLUCINATION: Never guess.
4. LINKS: Always use [View Product](URL). Never show raw URLs.
5. MEDICAL SAFETY: If a medical condition is mentioned, say:
   "This is a cosmetic product and is not intended to treat medical conditions."

🟢 CONVERSATION INTELLIGENCE:
- Greetings & small talk → respond politely, no product push.
- General questions (shipping, support) → use BRAND DETAILS.
- Product questions → follow CURRENT SITUATION logic.

🔵 SEARCH ENGINE STATUS:
{search_status}

{shop_context}

{off_topic_instruction}

CURRENT SITUATION:
{state_instruction}

PRODUCT DATA (Single Source of Truth):
{product_text}
"""

        # 8. Message Assembly
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-4:]:
            messages.append(msg)
        messages.append({"role": "user", "content": query})

        # 9. LLM Call with Cascade Fallback
        last_error = None
        for model in self.model_cascade:
            try:
                chat_completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=600
                )
                return chat_completion.choices[0].message.content
            except (RateLimitError, APIError, Exception) as e:
                last_error = e
                continue

        if last_error:
            traceback.print_exc()

        return "I apologize, but the system is currently busy. Please try again shortly."
