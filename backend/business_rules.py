import re
from typing import List
from .models import ProductVariant, ProductContext

class BusinessRules:
    
    # ---------------------------------------------------------
    # 1. STOCK AVAILABILITY RULES
    # ---------------------------------------------------------
    @staticmethod
    def get_stock_status(variants: List[ProductVariant]) -> str:
        total_qty = sum(v.inventory_qty for v in variants)
        can_continue = any(v.inventory_policy == 'continue' for v in variants)
        
        if total_qty > 0:
            return "In Stock" 
        elif can_continue:
            return "Available (Made to order)"
        else:
            return "Out of Stock"

    # ---------------------------------------------------------
    # 2. SAFETY & MEDICAL RULES
    # ---------------------------------------------------------
    @staticmethod
    def is_sensitive_query(query: str) -> bool:
        """Detects medical/safety keywords."""
        triggers = [
            r"cure", r"treat", r"heal", r"medicine", r"doctor", 
            r"prescription", r"eczema", r"psoriasis", r"acne", 
            r"infection", r"inflammation", r"dermatitis", r"rosacea",
            r"cancer", r"disease", r"virus", r"pain"
        ]
        pattern = "|".join(triggers)
        return bool(re.search(pattern, query.lower()))

    # ---------------------------------------------------------
    # 3. BRAND BOUNDARY RULES (NEW)
    # ---------------------------------------------------------
    @staticmethod
    def is_off_topic_query(query: str) -> bool:
        """
        Detects queries about competitors, revenue, or general knowledge 
        that should be refused.
        """
        triggers = [
            # Competitors / Marketplaces
            r"amazon", r"flipkart", r"myntra", r"nykaa", r"aliexpress", 
            r"ebay", r"walmart", r"sephora", r"body shop", r"burt's bees",
            r"now foods", r"gnc", r"nature's bounty",
            
            # Business / Corporate
            r"revenue", r"stock price", r"market cap", r"profit", 
            r"headquarters", r"ceo", r"founder", r"employees",
            r"companies that sell", r"other brands", r"competitors",
            
            # General Knowledge unrelated to brand product usage
            r"who is", r"what is the capital", r"weather", r"news"
        ]
        pattern = "|".join(triggers)
        return bool(re.search(pattern, query.lower()))

    # ---------------------------------------------------------
    # 4. PRODUCT PRIORITIZATION RULES
    # ---------------------------------------------------------
    @staticmethod
    def sort_products_for_context(products: List[ProductContext], query: str) -> List[ProductContext]:
        """Prioritizes Individual Items over Kits unless asked."""
        kit_keywords = ['ritual', 'kit', 'set', 'bundle', 'combo', 'pack', 'trio', 'duo']
        user_wants_kit = any(k in query.lower() for k in kit_keywords)

        if user_wants_kit:
            return sorted(products, key=lambda p: any(k in p.title.lower() for k in kit_keywords), reverse=True)
        return sorted(products, key=lambda p: any(k in p.title.lower() for k in kit_keywords))
