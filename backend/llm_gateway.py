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

        # 2. Determine Interaction State
        match_type = "direct"
        if sorted_products:
            match_type = sorted_products[0].match_quality  # direct / catalog / fallback

        # 3. Build PRODUCT DATA block
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

        # 4. Intent-based Instruction
        state_instruction = ""
        if match_type == "catalog":
            state_instruction = (
                "USER INTENT: Browsing catalog.\n"
                "ACTION: Enthusiastically recommend the top products below."
            )
        elif match_type == "fallback":
            state_instruction = (
                f"USER INTENT: Search failed for '{query}'.\n"
                "ACTION: Politely explain no exact match and suggest popular products."
            )
        else:
            state_instruction = (
                "USER INTENT: Specific product question.\n"
                "ACTION: Answer accurately using PRODUCT DATA only."
            )

        # 5. Off-topic / Competitor Guard
        off_topic_instruction = ""
        if BusinessRules.is_off_topic_query(query):
            off_topic_instruction = f"""
            🚨 OFF-TOPIC DETECTED
            ACTION: Refuse politely.
            RESPONSE:
            "I am the AI assistant for {brand_name} only.
            I cannot provide information about other brands, companies, or platforms."
            """

        # 6. Shop Context
        shop_context = f"""
        BRAND DETAILS:
        - Support Email: {shop_info.get('email', 'Check website')}
        - Phone: {shop_info.get('phone', 'Not listed')}
        - Domain: {shop_info.get('domain', '')}
        - Currency: {shop_info.get('currency', 'INR')}
        """

        # 7. SYSTEM PROMPT (Merged)
        system_prompt = f"""
        You are the official Product Support AI exclusively for the brand '{brand_name}'.

        🔴 NON-NEGOTIABLE RULES:
        1. BRAND ISOLATION: You ONLY know '{brand_name}'. Never mention competitors or marketplaces.
        2. SOURCE OF TRUTH: Answer strictly from PRODUCT DATA below.
           If data is missing, say: "I don't have that information."
        3. NO HALLUCINATION: Never guess.
        4. LINKS: Always use [View Product](URL). Never show raw URLs.
        5. MEDICAL SAFETY: If a medical condition is mentioned, say:
           "This is a cosmetic product and is not intended to treat medical conditions."

        🟢 CONVERSATION RULES:
        - Be helpful, professional, concise.
        - Guide the user if no product matches.
        - Recommend enthusiastically when appropriate.

        🔵 SHOP SUPPORT:
        - For refunds/support/contact, use BRAND DETAILS only.

        {shop_context}

        🔵 CONTEXT:
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

        # 9. LLM Call with Fallback
        last_error = None
        for model in self.model_cascade:
            try:
                chat_completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=600
                )
                return chat_completion.choices[0].message.content
            except (RateLimitError, APIError, Exception) as e:
                last_error = e
                continue

        if last_error:
            traceback.print_exc()

        return "I apologize, but the system is currently busy. Please try again shortly."
