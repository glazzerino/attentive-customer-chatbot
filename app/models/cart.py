import uuid
from typing import Optional, Dict, Any, List

from app.models.database import database
from app.models.product import Product


class CartItem:
    """Cart item model representing a product in a cart"""

    def __init__(self, id: str, conversation_id: str, product_id: str, quantity: int):
        self.id = id
        self.conversation_id = conversation_id
        self.product_id = product_id
        self.quantity = quantity
        self.product = None  # Populated on demand

    async def get_product(self) -> Optional[Product]:
        """Load the associated product"""
        if not self.product:
            self.product = await Product.get_by_id(self.product_id)
        return self.product

    def to_dict(self) -> Dict[str, Any]:
        """Convert cart item to dictionary"""
        result = {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
        }

        if self.product:
            result["product"] = self.product.to_dict()

        return result


class Cart:
    """Shopping cart for a conversation session"""

    @classmethod
    async def get_items(cls, conversation_id: str) -> List[CartItem]:
        """Get all items in a cart for a conversation"""
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM cart_items WHERE conversation_id = ?", (conversation_id,)
        )

        items = []
        for row in cursor.fetchall():
            item = CartItem(
                id=row['id'],
                conversation_id=row['conversation_id'],
                product_id=row['product_id'],
                quantity=row['quantity'],
            )
            # Load the product
            await item.get_product()
            items.append(item)

        return items

    @classmethod
    async def add_item(
        cls, conversation_id: str, product_id: str, quantity: int = 1
    ) -> CartItem:
        """Add an item to the cart"""
        conn = database.get_connection()
        cursor = conn.cursor()

        # Check if product exists
        product = await Product.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Check if item already in cart
        cursor.execute(
            "SELECT * FROM cart_items WHERE conversation_id = ? AND product_id = ?",
            (conversation_id, product_id),
        )

        existing_item = cursor.fetchone()

        if existing_item:
            # Update quantity
            new_quantity = existing_item['quantity'] + quantity
            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing_item['id']),
            )

            item = CartItem(
                id=existing_item['id'],
                conversation_id=conversation_id,
                product_id=product_id,
                quantity=new_quantity,
            )
        else:
            # Add new item
            item_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO cart_items (id, conversation_id, product_id, quantity) VALUES (?, ?, ?, ?)",
                (item_id, conversation_id, product_id, quantity),
            )

            item = CartItem(
                id=item_id,
                conversation_id=conversation_id,
                product_id=product_id,
                quantity=quantity,
            )

        conn.commit()
        item.product = product
        return item

    @classmethod
    async def remove_item(
        cls, conversation_id: str, product_id: str, quantity: Optional[int] = None
    ) -> bool:
        """Remove an item from the cart"""
        conn = database.get_connection()
        cursor = conn.cursor()

        # Check if item exists in cart
        cursor.execute(
            "SELECT * FROM cart_items WHERE conversation_id = ? AND product_id = ?",
            (conversation_id, product_id),
        )

        existing_item = cursor.fetchone()

        if not existing_item:
            return False

        if quantity is None or quantity >= existing_item['quantity']:
            # Remove item completely
            cursor.execute(
                "DELETE FROM cart_items WHERE id = ?", (existing_item['id'],)
            )
        else:
            # Decrease quantity
            new_quantity = existing_item['quantity'] - quantity
            cursor.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (new_quantity, existing_item['id']),
            )

        conn.commit()
        return True

    @classmethod
    async def clear(cls, conversation_id: str) -> None:
        """Clear all items from the cart"""
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM cart_items WHERE conversation_id = ?", (conversation_id,)
        )

        conn.commit()

    @classmethod
    async def calculate_total(cls, conversation_id: str) -> float:
        """Calculate the total price of items in the cart"""
        items = await cls.get_items(conversation_id)
        total = 0.0

        for item in items:
            if item.product:
                total += item.product.price * item.quantity

        return total
