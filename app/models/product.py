import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.database import database


class Product:
    """Product model representing an item for sale"""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        price: float,
        image_url: Optional[str] = None,
        in_stock: bool = True,
        categories: Optional[List[str]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.image_url = image_url
        self.in_stock = in_stock
        self.categories = categories or []

    @classmethod
    async def create(
        cls,
        name: str,
        description: str,
        price: float,
        image_url: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ) -> "Product":
        """Create a new product"""
        conn = database.get_connection()
        cursor = conn.cursor()

        product_id = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO products (id, name, description, price, image_url, in_stock) VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, name, description, price, image_url, True),
        )

        # Add categories if provided
        if categories:
            for category in categories:
                cursor.execute(
                    "INSERT INTO product_categories (product_id, category) VALUES (?, ?)",
                    (product_id, category),
                )

        conn.commit()

        return Product(
            id=product_id,
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            in_stock=True,
            categories=categories or [],
        )

    @classmethod
    async def get_by_id(cls, product_id: str) -> Optional["Product"]:
        """Get a product by ID"""
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))

        product_data = cursor.fetchone()
        if not product_data:
            return None

        # Get categories
        cursor.execute(
            "SELECT category FROM product_categories WHERE product_id = ?",
            (product_id,),
        )

        categories = [row["category"] for row in cursor.fetchall()]

        return Product(
            id=product_data["id"],
            name=product_data["name"],
            description=product_data["description"],
            price=product_data["price"],
            image_url=product_data["image_url"],
            in_stock=bool(product_data["in_stock"]),
            categories=categories,
        )

    @classmethod
    async def search(
        cls, query: str, category: Optional[str] = None, limit: int = 10
    ) -> List["Product"]:
        """Search for products by name, description, or category"""
        conn = database.get_connection()
        cursor = conn.cursor()

        if category:
            # Search within specific category
            cursor.execute(
                """
				SELECT p.* FROM products p
				JOIN product_categories pc ON p.id = pc.product_id
				WHERE (p.name LIKE ? OR p.description LIKE ?) AND pc.category = ?
				LIMIT ?
				""",
                (f"%{query}%", f"%{query}%", category, limit),
            )
        else:
            # Search across all products
            cursor.execute(
                """
				SELECT * FROM products
				WHERE name LIKE ? OR description LIKE ?
				LIMIT ?
				""",
                (f"%{query}%", f"%{query}%", limit),
            )

        products = []
        for row in cursor.fetchall():
            # Get categories for this product
            cursor.execute(
                "SELECT category FROM product_categories WHERE product_id = ?",
                (row["id"],),
            )
            categories = [cat_row["category"] for cat_row in cursor.fetchall()]

            products.append(
                Product(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    price=row["price"],
                    image_url=row["image_url"],
                    in_stock=bool(row["in_stock"]),
                    categories=categories,
                )
            )

        return products

    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "image_url": self.image_url,
            "in_stock": self.in_stock,
            "categories": self.categories,
        }
