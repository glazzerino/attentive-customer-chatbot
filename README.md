# WhatsApp E-Commerce Bot

A WhatsApp-based e-commerce solution leveraging Large Language Model (LLM) technology. This system enables users to browse products, add items to cart, and complete purchases through a conversational interface.

## Features

- WhatsApp messaging integration via Twilio
- Product search and browsing
- Shopping cart management
- Order processing
- Conversational UI powered by Anthropic Claude

## System Architecture

The system is built with the following components:

- **Messaging Platform Adapters**: Abstraction layer for messaging platforms
- **API Gateway**: FastAPI entry point for all messaging interactions
- **Message Queue**: Async message processing buffer
- **Message Processor**: Process incoming messages
- **Product Search Service**: Search capabilities across product catalog
- **Bot Engine**: Core conversational logic using LLM
- **Database Layer**: SQLite storage
- **Order Service**: Order management and payment processing

## Getting Started

### Prerequisites

- Python 3.9+
- Twilio account
- Anthropic API key

### Installation

1. Clone the repository
2. Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the template:

```bash
cp .env.example .env
```

5. Fill in your credentials in the `.env` file

### Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## Development

To set up your development environment:

1. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

2. Run tests:

```bash
pytest
```

## API Endpoints

- `POST /webhook/whatsapp`: Webhook for Twilio WhatsApp
- `GET /health`: Health check endpoint

## License

This project is licensed under the MIT License - see the LICENSE file for details.