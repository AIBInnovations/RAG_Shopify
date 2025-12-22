import pandas as pd
from bs4 import BeautifulSoup
import os
import re
from typing import List, Dict, Optional, Any
from .models import ProductContext, ProductVariant
from .shopify_client import ShopifyClient

class MultiTenantDataEngine:
    def __init__(self):
        self.brand_datasets: Dict[str, pd.DataFrame] = {}
        self.shopify_clients: Dict[str, ShopifyClient] = {}
        self.live_cache: Dict[str, List[ProductContext]] = {}
        self.shop_info_cache: Dict[str, Dict[str, Any]] = {} # New Cache for Brand Details
        self.column_maps: Dict[str, Dict[str, str]] = {}
        
        self.brand_metadata = {
    "miloe": {
        "file": "data/products_export_1.csv",
        "domain": "miloe.in",
        "api_env_key": "MILOE_ACCESS_TOKEN", 
        "shop_domain_env": "MILOE_SHOPIFY_DOMAIN"
    },  # ✅ MISSING COMMA FIXED
    
    "cristello": {
        "file": "data/products_export_2.csv", 
        "domain": "cristello.in",
        "api_env_key": "CRISTELLO_ACCESS_TOKEN", 
        "shop_domain_env": "CRISTELLO_SHOPIFY_DOMAIN"
    }
}

        self.CONTEXT_INTENTS = {'ingredients', 'description', 'price', 'cost', 'details', 'tell me more', 'specs', 'info'}
        self.PROMO_INTENTS = {'sale', 'offers', 'discounts', 'deals', 'promotion', 'cheap', 'save'}
        self.STOP_WORDS = {'i', 'want', 'need', 'to', 'buy', 'get', 'looking', 'for', 'show', 'me', 'the', 'a', 'an', 'only', 'just', 'with', 'in', 'products', 'product', 'is', 'are', 'there', 'any', 'do', 'you', 'have'}
        self.SYNONYMS = {
            "hair": ["shampoo", "conditioner", "mask", "oil", "scalp"],
            "face": ["wash", "serum", "moisturizer", "sunscreen", "gel", "cream"],
            "skin": ["wash", "serum", "moisturizer", "sunscreen", "body"],
            "clean": ["wash", "cleanser", "soap", "bar"]
        }
        self._initialize_sources()

    def _initialize_sources(self):
        for brand, meta in self.brand_metadata.items():
            api_key = os.getenv(meta.get("api_env_key", ""))
            domain = os.getenv(meta.get("shop_domain_env", ""))
            
            # API Initialization
            if api_key and domain:
                try:
                    print(f"🔌 Connecting to Shopify Live API for {brand}...")
                    client = ShopifyClient(domain, api_key)
                    
                    # 1. Fetch Products
                    products = client.fetch_all_products()
                    
                    # 2. Fetch Shop Info (Contact, Name, etc.)
                    shop_info = client.fetch_shop_details()
                    
                    if products:
                        self.shopify_clients[brand] = client
                        self.live_cache[brand] = products
                        self.shop_info_cache[brand] = shop_info
                        print(f"✨ {brand} is running in TRUE LIVE mode ({len(products)} products).")
                        print(f"   ℹ️  Store Contact: {shop_info.get('email')}")
                        continue 
                except Exception as e:
                    print(f"⚠️ API Init Failed for {brand}: {e}")

            # CSV Initialization
            if os.path.exists(meta['file']):
                print(f"📂 Loading CSV fallback for {brand}...")
                self._load_csv(brand, meta['file'])
                # Mock shop info for CSV brands if needed
                self.shop_info_cache[brand] = {
                    "name": brand.capitalize(),
                    "email": "Not specified (CSV Mode)",
                    "domain": meta['domain']
                }

    def get_shop_details(self, brand_id: str) -> Dict[str, Any]:
        """Returns cached shop details (email, phone, etc)"""
        return self.shop_info_cache.get(brand_id, {})

    # ... [Rest of the file: _load_csv, _clean_html, search_products, etc. remains UNCHANGED] ...
    # (Reuse the robust search logic from the previous step)
    def _load_csv(self, brand, filepath):
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str).fillna("")
            df.columns = df.columns.str.strip()
            self.brand_datasets[brand] = df
            cols = df.columns
            self.column_maps[brand] = {
                'inventory': next((c for c in ['Variant Inventory Qty', 'Qty', 'Stock'] if c in cols), None),
                'price': next((c for c in ['Variant Price', 'Price'] if c in cols), 'Variant Price'),
                'body': next((c for c in ['Body (HTML)', 'Description'] if c in cols), 'Body (HTML)'),
                'seo': next((c for c in ['SEO Description', 'Meta Description'] if c in cols), None)
            }
        except Exception as e:
            print(f"❌ Error loading CSV for {brand}: {e}")

    def _clean_html(self, html_content: str) -> str:
        if not html_content: return ""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            return re.sub(r'\n\s*\n', '\n', soup.get_text(separator="\n").strip())[:1500]
        except: return str(html_content)[:1500]

    def _normalize_text(self, text: str) -> str:
        return re.sub(r'[^a-z0-9]', '', str(text).lower())

    def _get_featured_products(self, brand_id: str, limit: int = 5) -> List[ProductContext]:
        products = []
        if brand_id in self.live_cache:
            products = self.live_cache[brand_id][:limit+2]
        else:
            df = self.brand_datasets.get(brand_id)
            if df is not None:
                for h in df['Handle'].unique()[:limit+2]:
                    p = self.get_product_by_handle_csv(brand_id, h)
                    if p: products.append(p)
        
        individual = [p for p in products if not self._is_kit(p.title)]
        selected = (individual + products)[:limit]
        for p in selected: p.match_quality = "fallback"
        return selected

    def _get_sale_products(self, brand_id: str, limit: int = 5) -> List[ProductContext]:
        if brand_id in self.live_cache:
            return [p for p in self.live_cache[brand_id] if "ON SALE" in p.price_range][:limit]
        return self._get_featured_products(brand_id)

    def _expand_query(self, query_tokens: List[str]) -> List[str]:
        expanded = set(query_tokens)
        for token in query_tokens:
            if token in self.SYNONYMS:
                expanded.update(self.SYNONYMS[token])
        return list(expanded)

    def search_products(self, brand_id: str, query: str, last_handle: Optional[str] = None) -> List[ProductContext]:
        raw_query = query.lower().strip()
        if any(k in raw_query for k in self.PROMO_INTENTS):
            results = self._get_sale_products(brand_id)
            for p in results: p.match_quality = "direct"
            return results
        if last_handle and any(k in raw_query for k in self.CONTEXT_INTENTS) and len(raw_query.split()) < 6:
            if brand_id in self.live_cache:
                p = next((x for x in self.live_cache[brand_id] if x.handle == last_handle), None)
                if p: 
                    p.match_quality = "direct"
                    return [p]
            else:
                p = self.get_product_by_handle_csv(brand_id, last_handle)
                if p: 
                    p.match_quality = "direct"
                    return [p]
        generic_keywords = ['products', 'catalog', 'list', 'show me', 'what do you have', 'collection', 'offer']
        if (any(k in raw_query for k in generic_keywords) and len(raw_query.split()) < 10) or raw_query in ["products", "all products"]:
            results = self._get_featured_products(brand_id)
            for p in results: p.match_quality = "catalog"
            return results
        tokens = [w for w in raw_query.split() if w not in self.STOP_WORDS and w not in self.CONTEXT_INTENTS]
        search_terms = self._expand_query(tokens)
        cleaned_query = "".join(tokens)
        if not cleaned_query: 
            results = self._get_featured_products(brand_id)
            for p in results: p.match_quality = "catalog"
            return results
        results = []
        if brand_id in self.live_cache:
            candidates = []
            for p in self.live_cache[brand_id]:
                score = 0
                norm_title = self._normalize_text(p.title)
                norm_tags = self._normalize_text(" ".join(p.tags))
                for term in search_terms:
                    if term in norm_title: score += 10
                    if term in norm_tags: score += 5
                if score > 0: candidates.append((score, p))
            candidates.sort(key=lambda x: x[0], reverse=True)
            results = [x[1] for x in candidates]
        else:
            df = self.brand_datasets.get(brand_id)
            if df is not None:
                unique_products = df.groupby('Handle').first().reset_index()
                unique_products['norm_text'] = unique_products['Title'].apply(self._normalize_text) + " " + unique_products['Tags'].apply(self._normalize_text)
                matches = pd.DataFrame()
                for term in search_terms:
                    matches = pd.concat([matches, unique_products[unique_products['norm_text'].str.contains(term)]])
                if not matches.empty:
                    matches = matches.drop_duplicates(subset=['Handle'])
                    for handle in matches['Handle'].head(5):
                        p = self.get_product_by_handle_csv(brand_id, handle)
                        if p: results.append(p)
        if results:
            for p in results: p.match_quality = "direct"
            if not self._is_kit(raw_query):
                results.sort(key=lambda p: self._is_kit(p.title))
            return results[:4]
        else:
            fallback_results = self._get_featured_products(brand_id)
            for p in fallback_results: p.match_quality = "fallback"
            return fallback_results

    def _is_kit(self, title: str) -> bool:
        kit_keywords = ['ritual', 'kit', 'set', 'bundle', 'combo', 'pack']
        return any(k in title.lower() for k in kit_keywords)

    def get_product_by_handle_csv(self, brand_id: str, handle: str) -> Optional[ProductContext]:
        df = self.brand_datasets.get(brand_id)
        if df is None: return None
        rows = df[df['Handle'] == handle]
        if rows.empty: return None
        base_row = rows.iloc[0]
        col_map = self.column_maps[brand_id]
        variants = []
        prices = []
        for _, row in rows.iterrows():
            qty = 100
            try: qty = int(float(str(row.get(col_map['inventory'] or '','0')).strip()))
            except: pass
            raw_price = str(row.get(col_map['price'], '0')).strip()
            try:
                p_val = re.sub(r'[^\d.]', '', raw_price)
                if p_val: prices.append(float(p_val))
            except: pass
            variants.append(ProductVariant(
                id=str(row.get('Variant SKU', '')),
                title=f"{row.get('Option1 Value', '')}".strip(),
                price=raw_price,
                inventory_qty=qty,
                inventory_policy=str(row.get('Variant Inventory Policy', 'deny')).lower(),
                sku=str(row.get('Variant SKU', ''))
            ))
        price_disp = f"{int(min(prices))}" if prices and min(prices)==max(prices) else "Not specified"
        desc = self._clean_html(base_row.get(col_map['body'], ''))
        return ProductContext(
            handle=handle,
            title=base_row['Title'],
            description=desc,
            tags=str(base_row['Tags']).split(','),
            vendor=base_row['Vendor'],
            variants=variants,
            url=f"https://{self.brand_metadata[brand_id]['domain']}/products/{handle}",
            price_range=price_disp,
            match_quality="direct"
        )
