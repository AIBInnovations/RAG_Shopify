import os
import traceback
from groq import Groq, RateLimitError, APIError
from typing import List, Dict
from .models import ProductContext
from .business_rules import BusinessRules

class LLMGateway:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key: print("❌ CRITICAL: GROQ_API_KEY missing.")
        self.client = Groq(api_key=api_key)
        
        self.model_cascade = [
            "llama-3.3-70b-versatile",
            "deepseek-r1-distill-llama-70b",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant"
        ]

    def generate_response(self, query: str, context_products: List[ProductContext], history: List[Dict], brand_name: str) -> str:
        # 1. Sort
        sorted_products = BusinessRules.sort_products_for_context(context_products, query)
        
        # 2. Determine Interaction State
        match_type = "direct"
        if sorted_products:
            match_type = sorted_products[0].match_quality 

        # 3. Build Data Block
        product_text = ""
        if not sorted_products:
            product_text = "NO MATCHING PRODUCTS FOUND IN CATALOG."
        else:
            for p in sorted_products:
                stock_status = BusinessRules.get_stock_status(p.variants)
                sale_tag = "🔥 ON SALE" if "ON SALE" in p.price_range else ""
                
                # Tags injected for reasoning
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

        # 4. Check for Off-Topic / Competitors
        off_topic_instruction = ""
        if BusinessRules.is_off_topic_query(query):
            off_topic_instruction = f"""
            🚨 ALERT: The user is asking about competitors, general companies, or business metrics (revenue, other brands).
            ACTION: REFUSE to answer. State clearly: "I am the AI assistant for {brand_name} only. I cannot provide information about other companies or platforms."
            DO NOT list other companies.
            """

        # 5. THE BRAND-ISOLATED PROMPT
        system_prompt = f"""
        You are the official Product Support Assistant exclusively for the brand '{brand_name}'.
        You are NOT a general knowledge assistant. You do not know about Amazon, AliExpress, or other brands.

        🔴 NEGATIVE CONSTRAINTS (NEVER VIOLATE):
        1. BRAND ISOLATION: Do NOT mention any other brand, company, or marketplace (e.g., Amazon, AliExpress, Nivea). If asked, say you only know '{brand_name}'.
        2. NO GENERAL KNOWLEDGE: Do not answer questions about geography, math, revenue, or history. Only answer about '{brand_name}' products.
        3. NO HALLUCINATION: If the 'PRODUCT DATA' section below is empty or doesn't contain the answer, say "I don't have that information." Do NOT make it up.
        4. STRICT LINKS: Use format: [View Product](URL). Never raw URLs.

        🟢 CONVERSATION RULES:
        1. HELP FIRST: Identify what the user wants regarding *our* products.
        2. MEDICAL SAFETY: If user mentions medical conditions, state: "This is a cosmetic product, not intended to treat medical conditions."
        3. GUIDE THE USER: If no product matches, ask about their specific skin/hair concern.

        🔵 CONTEXT INSTRUCTIONS:
        {off_topic_instruction}
        
        - IF 'PRODUCT DATA' IS EMPTY:
          - Politely say: "I couldn't find a product matching that description in our catalog."
          - Ask: "Could you tell me more about what you're looking for?"
        
        - IF 'PRODUCT DATA' HAS ITEMS:
          - Use the data to answer the user's question.
          - If the user asks for a list, recommend the top items enthusiastically.

        PRODUCT DATA (Source of Truth):
        {product_text}
        """

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-4:]: messages.append(msg)
        messages.append({"role": "user", "content": query})

        # 5. API Call
        last_error = None
        for model in self.model_cascade:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages, model=model, temperature=0.0, max_tokens=600
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                last_error = e
                continue
        
        if last_error: traceback.print_exc()
        return "I apologize, but I am currently experiencing high traffic."