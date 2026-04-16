from params import *
import requests
import json

def get_search_suggestion(query):
    json_data = {
        'query': query,
        'pageNumber': 0,
        'mode': 'TYPED',
        'intentId': '4295ae68-3356-419e-b974-828c49fa429d',
    }

    response = requests.post(
        'https://bff-gateway.zepto.com/user-search-service/api/v3/search',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )

    if response.status_code != 200:
        return {"error": "Failed to fetch search suggestions"}
    
    data=response.json()
    items=data['layout'][0]['data']['resolver']['data']['items']
    if not items:
        return {"error": "No results found for the query"}
    
    first_suggestion=items[0]['name']


    return search_product(first_suggestion)
    # layout[0].data.resolver.data.items[0].name
    
def search_product(query):
    json_data = {
    'query': query,
    'pageNumber': 0,
    'intentId': '13263797-5f21-4cc5-9c96-3011d833df60',
    'mode': 'AUTOSUGGEST',
    'userSessionId': '7cd52164-c75a-4efc-b5a1-161549e77ca0',
    }
    response = requests.post(
        'https://bff-gateway.zepto.com/user-search-service/api/v3/search',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )
    
    product_response=response.json()

    return parse_product_response(product_response,query)

def _first(items, default=None):
    if isinstance(items, list) and items:
        return items[0]
    return default


def _to_rupees(value):
    if value is None:
        return None
    return round(value / 100, 2)


def _extract_badges(meta):
    badges = []
    tags_v2 = (meta or {}).get("tagsV2") or {}

    for tag in tags_v2.values():
        tag_name = tag.get("tagName")
        tag_type = tag.get("tagType")
        if tag_name and tag_type != "DISCOUNT":
            badges.append(tag_name)

    return badges


def extract_listing_products(response_path, query):
    payload = response_path
    products = []

    item_number = 1
    base_url="https://cdn.zeptonow.com/production/"
    for widget in payload.get("layout", []):
        resolver = widget.get("data", {}).get("resolver", {})
        if resolver.get("type") != "product_grid":
            continue

       
        for card in resolver.get("data", {}).get("items", []):
            product_response = card.get("productResponse") or {}
            product = product_response.get("product") or {}
            product_variant = product_response.get("productVariant") or {}
            meta = product_response.get("meta") or {}
            image = _first(product_variant.get("images"), {}) or {}
            rating_summary = product_variant.get("ratingSummary") or {}

            selling_price = product_response.get("sellingPrice")
            if selling_price is None:
                selling_price = product_response.get("discountedSellingPrice")

            mrp = product_response.get("mrp")
            badges = _extract_badges(meta)
            if "Sponsored" in badges:
                item_number += 1
                continue
            products.append(
                {
                    "item_number": item_number,
                    "product_id": product.get("id"),
                    "product_name": product.get("name"),
                    "brand": product.get("brand"),
                    "pack_size": product_variant.get("formattedPacksize"),
                    "current_price": _to_rupees(selling_price),
                    "mrp": _to_rupees(mrp),
                    "discount_percent": product_response.get("discountPercent"),
                    "savings": _to_rupees(mrp - selling_price) if mrp is not None and selling_price is not None else None,
                    "rating": rating_summary.get("averageRating"),
                    "rating_count": rating_summary.get("totalRatings"),
                    "badges": badges,
                    "image_url": base_url+image.get("path"),
                }
            )
            item_number += 1

    return {"First_Suggestion": query, "products": products}

def parse_product_response(product_response, query):
    products = extract_listing_products(product_response, query)
    return products
 