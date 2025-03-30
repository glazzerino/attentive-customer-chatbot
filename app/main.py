import os
from fastapi import FastAPI
from dotenv import load_dotenv

from app.api.webhook import router as webhook_router

load_dotenv()

app = FastAPI(title="WhatsApp E-Commerce Bot")

app.include_router(webhook_router)

@app.get("/health")
async def health_check():
	return {"status": "ok"}
