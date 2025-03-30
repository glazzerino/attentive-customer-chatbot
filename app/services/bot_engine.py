import json
from typing import Dict, Any, List, Optional
import uuid

from app.services.llm_client import LLMClient
from app.models.product import Product
from app.models.cart import Cart
from app.models.order import Order

class BotEngine:
    """Core conversational logic using LLM"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def process_function_call(self, function_name: str, params: Dict[str, Any], conversation_id: str, user_id: str) -> Dict[str, Any]:
        """Process a function call from the LLM"""
        
        # Search products
        if function_name == "search_products":
            query = params.get("query", "")
            category = params.get("category", None)
            limit = int(params.get("limit", 10))
            
            products = await Product.search(query, category, limit)
            return {
                "success": True,
                "data": [product.to_dict() for product in products]
            }
        
        # Get product details
        elif function_name == "get_product_details":
            product_id = params.get("product_id", "")
            
            product = await Product.get_by_id(product_id)
            if not product:
                return {
                    "success": False,
                    "error": f"Product {product_id} not found"
                }
            
            return {
                "success": True,
                "data": product.to_dict()
            }
        
        # Add to cart
        elif function_name == "add_to_cart":
            product_id = params.get("product_id", "")
            quantity = int(params.get("quantity", 1))
            
            try:
                cart_item = await Cart.add_item(conversation_id, product_id, quantity)
                
                # Get all items for display
                cart_items = await Cart.get_items(conversation_id)
                total = await Cart.calculate_total(conversation_id)
                
                return {
                    "success": True,
                    "data": {
                        "added_item": cart_item.to_dict(),
                        "cart": [item.to_dict() for item in cart_items],
                        "total": total
                    }
                }
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # View cart
        elif function_name == "view_cart":
            cart_items = await Cart.get_items(conversation_id)
            total = await Cart.calculate_total(conversation_id)
            
            return {
                "success": True,
                "data": {
                    "items": [item.to_dict() for item in cart_items],
                    "total": total
                }
            }
        
        # Remove from cart
        elif function_name == "remove_from_cart":
            product_id = params.get("product_id", "")
            quantity = params.get("quantity", None)
            if quantity:
                quantity = int(quantity)
            
            success = await Cart.remove_item(conversation_id, product_id, quantity)
            
            if success:
                # Get updated cart
                cart_items = await Cart.get_items(conversation_id)
                total = await Cart.calculate_total(conversation_id)
                
                return {
                    "success": True,
                    "data": {
                        "items": [item.to_dict() for item in cart_items],
                        "total": total
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Product {product_id} not found in cart"
                }
        
        # Create order
        elif function_name == "create_order":
            order = await Order.create_from_cart(user_id, conversation_id)
            
            if not order:
                return {
                    "success": False,
                    "error": "Cart is empty"
                }
            
            return {
                "success": True,
                "data": order.to_dict()
            }
        
        # Get payment link (placeholder for now)
        elif function_name == "get_payment_link":
            order_id = params.get("order_id", "")
            
            order = await Order.get_by_id(order_id)
            if not order:
                return {
                    "success": False,
                    "error": f"Order {order_id} not found"
                }
            
            # Placeholder for payment link
            payment_link = f"https://example.com/pay?order={order_id}"
            
            return {
                "success": True,
                "data": {
                    "payment_link": payment_link,
                    "order": order.to_dict()
                }
            }
        
        # Check order status
        elif function_name == "check_order_status":
            order_id = params.get("order_id", "")
            
            order = await Order.get_by_id(order_id)
            if not order:
                return {
                    "success": False,
                    "error": f"Order {order_id} not found"
                }
            
            return {
                "success": True,
                "data": order.to_dict()
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown function {function_name}"
            }
    
    async def get_function_descriptions(self) -> List[Dict[str, Any]]:
        """Get function descriptions for LLM function calling"""
        return [
            {
                "name": "search_products",
                "description": "Search product catalog",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category to filter by"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_product_details",
                "description": "Get detailed information about a product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID"
                        }
                    },
                    "required": ["product_id"]
                }
            },
            {
                "name": "add_to_cart",
                "description": "Add product to cart",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to add"
                        }
                    },
                    "required": ["product_id"]
                }
            },
            {
                "name": "view_cart",
                "description": "View current cart contents",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "remove_from_cart",
                "description": "Remove product from cart",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to remove (leave empty to remove all)"
                        }
                    },
                    "required": ["product_id"]
                }
            },
            {
                "name": "create_order",
                "description": "Create order from cart",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_payment_link",
                "description": "Generate payment link",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID"
                        }
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "check_order_status",
                "description": "Check order status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID"
                        }
                    },
                    "required": ["order_id"]
                }
            }
        ]