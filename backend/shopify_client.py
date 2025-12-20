import requests
from typing import List, Dict, Optional
from .models import ProductContext, ProductVariant

class ShopifyClient:
    def __init__(self, domain: str, access_token: str):
        self.domain = domain.replace("https://", "").replace("/", "")
        self.base_url = f"https://{self.domain}/admin/api/2024-01"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }

    def _clean_html(self, raw_html: str) -> str:
        from bs4 import BeautifulSoup
        if not raw_html: return ""
        try:
            return BeautifulSoup(raw_html, "html.parser").get_text(separator="\n").strip()[:1000]
        except:
            return str(raw_html)[:1000]

    def fetch_all_products(self) -> List[ProductContext]:
        products = []
        url = f"{self.base_url}/products.json?limit=250&status=active"
        
        try:
            while url:
                print(f"🔄 Fetching page from Shopify ({self.domain})...")
                response = requests.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    print(f"❌ Shopify API Error: {response.status_code} - {response.text}")
                    break
                    
                data = response.json()
                
                for item in data.get('products', []):
                    try:
                        products.append(self._map_to_context(item))
                    except Exception as e:
                        print(f"⚠️ Skipping product {item.get('id')} due to validation error: {e}")
                
                link_header = response.headers.get('Link')
                url = None
                if link_header:
                    links = link_header.split(',')
                    for link in links:
                        if 'rel="next"' in link:
                            url = link.split(';')[0].strip('<> ')
            
            print(f"✅ Shopify Sync Complete: {len(products)} products fetched from {self.domain}")
            return products
            
        except Exception as e:
            print(f"❌ Shopify Sync Failed: {e}")
            return []

    def _map_to_context(self, item: Dict) -> ProductContext:
        variants = []
        prices = []
        compare_prices = []
        
        for v in item.get('variants', []):
            qty = v.get('inventory_quantity', 0)
            policy = v.get('inventory_policy', 'deny')
            
            # Handle Price (None check)
            p_val = v.get('price')
            price = float(p_val) if p_val is not None else 0.0
            
            c_val = v.get('compare_at_price')
            compare = float(c_val) if c_val is not None else 0.0
            
            prices.append(price)
            if compare > price:
                compare_prices.append(compare)

            # CRITICAL FIX: Handle None for Title/SKU
            v_title = str(v.get('title') or "")
            v_sku = str(v.get('sku') or "")

            variants.append(ProductVariant(
                id=str(v['id']),
                title=v_title,
                price=str(int(price)), 
                inventory_qty=qty,
                inventory_policy=policy,
                sku=v_sku
            ))

        # Price Range & Sale Logic
        if prices:
            min_p, max_p = min(prices), max(prices)
            price_str = f"{int(min_p)}" if min_p == max_p else f"{int(min_p)} - {int(max_p)}"
        else:
            price_str = "Not specified"
        
        is_on_sale = any(c > p for c, p in zip(compare_prices, prices)) if compare_prices else False
        sale_tag = "🔥 ON SALE! " if is_on_sale else ""
        
        handle = item.get('handle', '') or "unknown"
        full_url = f"https://{self.domain}/products/{handle}"

        return ProductContext(
            handle=handle,
            title=str(item.get('title') or ""),
            description=self._clean_html(item.get('body_html', '')),
            tags=str(item.get('tags', '')).split(', '),
            vendor=str(item.get('vendor', '')),
            variants=variants,
            url=full_url,             
            price_range=f"{sale_tag}{price_str}", 
            ingredients="Not specified" 
        )