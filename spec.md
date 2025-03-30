# WhatsApp E-Commerce Bot: Technical Specification

## 1. System Overview

This document provides technical specifications for a WhatsApp-based e-commerce solution leveraging Large Language Model (LLM) technology. The system enables users to browse products, add items to cart, and complete purchases through a conversational interface.

The architecture emphasizes abstraction of third-party services to ensure vendor independence and extensibility.

## 2. System Architecture

### 2.1 Component Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Messaging      │    │  API Gateway    │    │  Message        │
│  Platform       ├───►│  + Webhook      ├───►│  Queue          │
│  Adapters       │    │  (FastAPI)      │    │  (Redis)        │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Database       │◄───┤ Product Search  │◄───┤  Message        │
│  (SQLite)       │    │    Service      │    │  Processor      │
└─────────────────┘    └────────▲────────┘    └─────────────────┘
        ▲                       │
        │               ┌───────┴────────┐
        │               │  Bot Engine    │
        │               │  + LLM Client  │
        │               └───────┬────────┘
        │                       │
        └───────────────┤  Order Service  │
                        │  + Payment      │
                        │  Abstraction    │
                        └─────────────────┘
```

### 2.2 Component Descriptions

#### 2.2.1 Messaging Platform Adapters
- **Purpose**: Provide abstraction layer for messaging platforms
- **Current Implementation**: Twilio WhatsApp integration
- **Abstraction Requirement**: Must be designed to allow for additional messaging platforms in the future

#### 2.2.2 API Gateway
- **Purpose**: Entry point for all messaging interactions
- **Technology**: FastAPI framework
- **Responsibilities**: Webhook handling, message routing, request validation

#### 2.2.3 Message Queue
- **Purpose**: Asynchronous message processing buffer
- **Technology**: Redis
- **Responsibilities**: Message queuing, worker distribution, retry handling

#### 2.2.4 Message Processor
- **Purpose**: Process incoming messages from queue
- **Responsibilities**: Context loading, LLM preparation, response handling

#### 2.2.5 Product Search Service
- **Purpose**: Provide search capabilities across product catalog
- **Responsibilities**: Keyword matching, category filtering, result ranking
- **Future Extensions**: Vector database integration for semantic search

#### 2.2.6 Bot Engine
- **Purpose**: Core conversational logic using LLM
- **Current Implementation**: Anthropic Claude API
- **Abstraction Requirement**: Must be designed to allow for alternative LLM providers
- **Responsibilities**: Context management, function calling, response generation

#### 2.2.7 Database Layer
- **Purpose**: Persistent storage for all system data
- **Technology**: SQLite (with schema designed for potential migration)
- **Responsibilities**: Data persistence, query handling

#### 2.2.8 Order Service
- **Purpose**: Handle order creation and payment processing
- **Responsibilities**: Order management, payment provider abstraction

## 3. Data Models

### 3.1 User Entity
- **phone_number**: String (Primary Key)
- **name**: String
- **created_at**: DateTime
- **last_interaction**: DateTime
- **active_conversation_id**: String (Optional)

### 3.2 Conversation Entity
- **id**: String (Primary Key)
- **user_id**: String (Foreign Key → User)
- **current_context**: String
- **active_product_id**: String (Optional)
- **cart**: Array of CartItems
- **created_at**: DateTime
- **updated_at**: DateTime

### 3.3 Message Entity
- **id**: String (Primary Key)
- **conversation_id**: String (Foreign Key → Conversation)
- **role**: String ("user" or "assistant")
- **content**: String
- **timestamp**: DateTime

### 3.4 Product Entity
- **id**: String (Primary Key)
- **name**: String
- **description**: String
- **price**: Decimal
- **categories**: Array of Strings
- **image_url**: String (Optional)
- **in_stock**: Boolean

### 3.5 Order Entity
- **id**: String (Primary Key)
- **user_id**: String (Foreign Key → User)
- **items**: Array of OrderItems
- **total_amount**: Decimal
- **status**: String
- **payment_info**: PaymentInfo Object
- **created_at**: DateTime
- **updated_at**: DateTime

### 3.6 OrderItem Entity
- **product_id**: String (Foreign Key → Product)
- **quantity**: Integer
- **unit_price**: Decimal

### 3.7 PaymentInfo Entity
- **provider**: String
- **payment_id**: String (Optional)
- **payment_link**: String (Optional)
- **status**: String
- **created_at**: DateTime
- **updated_at**: DateTime

## 4. Key Interfaces and Abstractions

### 4.1 Messaging Platform Interface
The system must abstract messaging platform interactions through a well-defined interface:

- **validate_webhook()**: Validate incoming webhook request
- **parse_message()**: Parse incoming message into standardized format
- **send_message()**: Send message to user
- **send_media()**: Send media to user

Initial implementation will be for Twilio WhatsApp, but the design must support additional platforms without core architecture changes.

### 4.2 LLM Provider Interface
The system must abstract LLM provider interactions through a well-defined interface:

- **generate_response()**: Generate response from LLM
- **execute_function_call()**: Process function calls from LLM
- **get_embeddings()**: Get vector embeddings for text (future use)

Initial implementation will be for Anthropic's Claude API, but the design must support alternative providers without core architecture changes.

### 4.3 Payment Provider Interface
The system must abstract payment processing through a well-defined interface:

- **generate_payment_link()**: Generate payment link for order
- **check_payment_status()**: Check status of payment

## 5. API Definitions

### 5.1 External APIs

#### 5.1.1 Webhook Endpoint
- **POST /webhook/{platform}**: Receive messages from messaging platforms

#### 5.1.2 Admin APIs
- **Product Management**: CRUD operations for product catalog
- **Order Management**: Order tracking and status updates

### 5.2 Internal APIs

#### 5.2.1 LLM Function Schema
The system requires the following function call capabilities from the LLM:

- **search_products**: Search product catalog
- **get_product_details**: Get detailed information about a product
- **add_to_cart**: Add product to cart
- **view_cart**: View current cart contents
- **remove_from_cart**: Remove product from cart
- **create_order**: Create order from cart
- **get_payment_link**: Generate payment link
- **check_order_status**: Check order status

## 6. Database Schema

### 6.1 Core Tables

#### 6.1.1 Users Table
- phone_number (PK)
- name
- created_at
- last_interaction
- active_conversation_id

#### 6.1.2 Conversations Table
- id (PK)
- user_id (FK)
- context
- active_product_id
- created_at
- updated_at

#### 6.1.3 Messages Table
- id (PK)
- conversation_id (FK)
- role
- content
- timestamp

#### 6.1.4 Products Table
- id (PK)
- name
- description
- price
- image_url
- in_stock

#### 6.1.5 Product Categories Table
- product_id (PK, FK)
- category (PK)

#### 6.1.6 Cart Items Table
- id (PK)
- conversation_id (FK)
- product_id
- quantity

#### 6.1.7 Orders Table
- id (PK)
- user_id (FK)
- total_amount
- status
- created_at
- updated_at

#### 6.1.8 Order Items Table
- id (PK)
- order_id (FK)
- product_id
- quantity
- unit_price

#### 6.1.9 Payments Table
- id (PK)
- order_id (FK)
- provider
- payment_id
- payment_link
- status
- created_at
- updated_at

## 7. Redis Data Structures

### 7.1 Message Queue
- **Key Structure**: LIST message_queue
- **Data Format**: JSON message details

### 7.2 Active Conversations Cache
- **Key Structure**: HASH conversation:{id}
- **Fields**: user_id, state, last_updated
- **TTL**: 24 hours of inactivity

### 7.3 Rate Limiting
- **Key Structure**: HASH rate_limit:{phone_number}
- **Fields**: count, reset_at
- **TTL**: 1 hour

## 8. Security Considerations

### 8.1 Data Protection
- Webhook validation for all incoming requests
- Encryption of sensitive user and payment data
- Proper error handling to prevent data leaks

### 8.2 Access Control
- Role-based access for admin interface
- API authentication for admin endpoints
- Secure storage of API keys and secrets

### 8.3 Rate Limiting
- Per-user and global rate limiting
- Protection against DoS attacks
- Graceful degradation under load

## 9. Scalability Considerations

### 9.1 Horizontal Scaling
- Stateless API Gateway design
- Multiple message processor instances
- Redis cluster for queue scaling

### 9.2 Performance Optimization
- Caching strategy for common responses
- Optimized LLM prompt design
- Efficient database querying

## 10. Technology Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: SQLite (designed for potential migration to PostgreSQL)
- **Caching/Queue**: Redis
- **LLM Provider**: Anthropic Claude API (with abstraction layer)
- **Messaging Service**: Twilio WhatsApp API (with abstraction layer)

## 11. Monitoring and Logging

### 11.1 System Metrics
- Request/response times
- Queue depths
- LLM token usage and costs
- Error rates

### 11.2 Business Metrics
- Conversation completion rates
- Order conversion rates
- User engagement metrics
- Product search effectiveness
