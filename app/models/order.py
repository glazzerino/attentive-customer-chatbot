import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.models.database import database
from app.models.cart import Cart, CartItem
from app.models.product import Product

class OrderItem:
	"""Order item model representing a product in an order"""
	
	def __init__(
		self,
		id: str,
		order_id: str,
		product_id: str,
		quantity: int,
		unit_price: float
	):
		self.id = id
		self.order_id = order_id
		self.product_id = product_id
		self.quantity = quantity
		self.unit_price = unit_price
		self.product = None  # Populated on demand
	
	async def get_product(self) -> Optional[Product]:
		"""Load the associated product"""
		if not self.product:
			self.product = await Product.get_by_id(self.product_id)
		return self.product
	
	def to_dict(self) -> Dict[str, Any]:
		"""Convert order item to dictionary"""
		result = {
			'id': self.id,
			'product_id': self.product_id,
			'quantity': self.quantity,
			'unit_price': self.unit_price,
			'total_price': self.quantity * self.unit_price
		}
		
		if self.product:
			result['product'] = self.product.to_dict()
			
		return result

class Order:
	"""Order model representing a completed purchase"""
	
	def __init__(
		self,
		id: str,
		user_id: str,
		total_amount: float,
		status: str,
		created_at: Optional[datetime] = None,
		updated_at: Optional[datetime] = None
	):
		self.id = id
		self.user_id = user_id
		self.total_amount = total_amount
		self.status = status
		self.created_at = created_at or datetime.now()
		self.updated_at = updated_at or datetime.now()
		self.items = []  # List of OrderItems
		self.payment = None  # Payment details
	
	@classmethod
	async def create_from_cart(cls, user_id: str, conversation_id: str) -> Optional['Order']:
		"""Create a new order from a cart"""
		conn = database.get_connection()
		cursor = conn.cursor()
		
		# Get cart items
		cart_items = await Cart.get_items(conversation_id)
		if not cart_items:
			return None
		
		# Calculate total
		total_amount = await Cart.calculate_total(conversation_id)
		
		# Create order
		order_id = str(uuid.uuid4())
		now = datetime.now().isoformat()
		
		cursor.execute(
			"INSERT INTO orders (id, user_id, total_amount, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
			(order_id, user_id, total_amount, "pending", now, now)
		)
		
		# Create order items
		order_items = []
		for cart_item in cart_items:
			if cart_item.product:
				item_id = str(uuid.uuid4())
				cursor.execute(
					"INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
					(item_id, order_id, cart_item.product_id, cart_item.quantity, cart_item.product.price)
				)
				
				order_item = OrderItem(
					id=item_id,
					order_id=order_id,
					product_id=cart_item.product_id,
					quantity=cart_item.quantity,
					unit_price=cart_item.product.price
				)
				order_item.product = cart_item.product
				order_items.append(order_item)
		
		# Clear the cart
		await Cart.clear(conversation_id)
		
		conn.commit()
		
		# Create and return the order
		order = Order(
			id=order_id,
			user_id=user_id,
			total_amount=total_amount,
			status="pending",
			created_at=datetime.fromisoformat(now),
			updated_at=datetime.fromisoformat(now)
		)
		order.items = order_items
		
		return order
	
	@classmethod
	async def get_by_id(cls, order_id: str) -> Optional['Order']:
		"""Get an order by ID"""
		conn = database.get_connection()
		cursor = conn.cursor()
		
		cursor.execute(
			"SELECT * FROM orders WHERE id = ?",
			(order_id,)
		)
		
		order_data = cursor.fetchone()
		if not order_data:
			return None
		
		# Create order
		order = Order(
			id=order_data['id'],
			user_id=order_data['user_id'],
			total_amount=order_data['total_amount'],
			status=order_data['status'],
			created_at=datetime.fromisoformat(order_data['created_at']),
			updated_at=datetime.fromisoformat(order_data['updated_at'])
		)
		
		# Get order items
		cursor.execute(
			"SELECT * FROM order_items WHERE order_id = ?",
			(order_id,)
		)
		
		items = []
		for row in cursor.fetchall():
			item = OrderItem(
				id=row['id'],
				order_id=order_id,
				product_id=row['product_id'],
				quantity=row['quantity'],
				unit_price=row['unit_price']
			)
			# Load the product
			await item.get_product()
			items.append(item)
		
		order.items = items
		
		# Get payment information (placeholder for now)
		# We'll implement the Payment model in the next phase
		
		return order
	
	@classmethod
	async def get_by_user(cls, user_id: str, limit: int = 10) -> List['Order']:
		"""Get orders for a user"""
		conn = database.get_connection()
		cursor = conn.cursor()
		
		cursor.execute(
			"SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
			(user_id, limit)
		)
		
		orders = []
		for row in cursor.fetchall():
			order = Order(
				id=row['id'],
				user_id=row['user_id'],
				total_amount=row['total_amount'],
				status=row['status'],
				created_at=datetime.fromisoformat(row['created_at']),
				updated_at=datetime.fromisoformat(row['updated_at'])
			)
			# Load order items
			cursor.execute(
				"SELECT * FROM order_items WHERE order_id = ?",
				(order.id,)
			)
			
			items = []
			for item_row in cursor.fetchall():
				item = OrderItem(
					id=item_row['id'],
					order_id=order.id,
					product_id=item_row['product_id'],
					quantity=item_row['quantity'],
					unit_price=item_row['unit_price']
				)
				items.append(item)
			
			order.items = items
			orders.append(order)
		
		return orders
	
	async def update_status(self, status: str) -> None:
		"""Update the order status"""
		conn = database.get_connection()
		cursor = conn.cursor()
		
		now = datetime.now().isoformat()
		self.status = status
		self.updated_at = datetime.fromisoformat(now)
		
		cursor.execute(
			"UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
			(status, now, self.id)
		)
		
		conn.commit()
	
	def to_dict(self) -> Dict[str, Any]:
		"""Convert order to dictionary"""
		return {
			'id': self.id,
			'user_id': self.user_id,
			'total_amount': self.total_amount,
			'status': self.status,
			'created_at': self.created_at.isoformat() if self.created_at else None,
			'updated_at': self.updated_at.isoformat() if self.updated_at else None,
			'items': [item.to_dict() for item in self.items]
		}
