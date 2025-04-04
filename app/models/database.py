import sqlite3
from typing import Dict, Any, List, Optional
from dotenv import dotenv_values


class Database:
    """SQLite database connection manager"""

    def __init__(self, db_path: str = None):
        config = dotenv_values()
        self.db_path = db_path or config.get("DATABASE_PATH")
        if not self.db_path:
            # Default to local file in project root if not specified
            self.db_path = "ecommerce_bot.db"
        self.conn = None
        self.create_tables()

    def get_connection(self):
        """Get a database connection"""
        if self.conn is None:
            # Ensure parent directory exists
            import os

            parent_dir = os.path.dirname(self.db_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path)
            # SQLite row_factory allows dictionary-style access with row['column_name']
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS users (
			phone_number TEXT PRIMARY KEY,
			name TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			active_conversation_id TEXT
		)
		"""
        )

        # Conversations table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS conversations (
			id TEXT PRIMARY KEY,
			user_id TEXT,
			context TEXT,
			active_product_id TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (user_id) REFERENCES users (phone_number)
		)
		"""
        )

        # Messages table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS messages (
			id TEXT PRIMARY KEY,
			conversation_id TEXT,
			role TEXT,
			content TEXT,
			phone_number TEXT,
			media_url TEXT,
			message_type TEXT DEFAULT 'text',
			platform TEXT DEFAULT 'whatsapp',
			metadata TEXT,
			raw_data TEXT,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (conversation_id) REFERENCES conversations (id)
		)
		"""
        )

        # Products table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS products (
			id TEXT PRIMARY KEY,
			name TEXT,
			description TEXT,
			price REAL,
			image_url TEXT,
			in_stock BOOLEAN
		)
		"""
        )

        # Product Categories table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS product_categories (
			product_id TEXT,
			category TEXT,
			PRIMARY KEY (product_id, category),
			FOREIGN KEY (product_id) REFERENCES products (id)
		)
		"""
        )

        # Cart Items table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS cart_items (
			id TEXT PRIMARY KEY,
			conversation_id TEXT,
			product_id TEXT,
			quantity INTEGER,
			FOREIGN KEY (conversation_id) REFERENCES conversations (id),
			FOREIGN KEY (product_id) REFERENCES products (id)
		)
		"""
        )

        # Orders table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS orders (
			id TEXT PRIMARY KEY,
			user_id TEXT,
			total_amount REAL,
			status TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (user_id) REFERENCES users (phone_number)
		)
		"""
        )

        # Order Items table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS order_items (
			id TEXT PRIMARY KEY,
			order_id TEXT,
			product_id TEXT,
			quantity INTEGER,
			unit_price REAL,
			FOREIGN KEY (order_id) REFERENCES orders (id),
			FOREIGN KEY (product_id) REFERENCES products (id)
		)
		"""
        )

        # Payments table
        cursor.execute(
            """
		CREATE TABLE IF NOT EXISTS payments (
			id TEXT PRIMARY KEY,
			order_id TEXT,
			provider TEXT,
			payment_id TEXT,
			payment_link TEXT,
			status TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (order_id) REFERENCES orders (id)
		)
		"""
        )

        conn.commit()


# Initialize the database
database = Database()
