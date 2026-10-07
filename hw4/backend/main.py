"""Campus Customs backend (FastAPI).

Routes:
- /api/products, /api/products/{id}  product catalogue + per-size stock
- /media/products/<file>             product images from data/products
- /api/auth/*                        signup / login / current user (auth.py)
- /api/chat                          PydanticAI shopping agent (agent.py)
- /api/chat/history                  logged-in shopper's saved chat (chat_history.py)

Run from inside the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import logging
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import chat_history
import images
import tools
from agent import run_chat
from auth import UserOut, current_user, optional_user
from auth import router as auth_router
from db import PRODUCTS_DIR
from models import ChatHistoryResponse, ChatRequest, ChatResponse, ProductCard

logger = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Image paths in the catalogue look like "products/<slug>.jpg", so serving
# data/products at /media/products lets the frontend use "/media/" + path.
app.mount("/media/products", StaticFiles(directory=PRODUCTS_DIR), name="product-images")
app.include_router(images.router)  # /media/display/products/<file>: storefront-ready copies
app.include_router(auth_router)


@app.on_event("startup")
def build_display_images() -> None:
    images.prewarm()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products", response_model=list[ProductCard])
def list_products(
    q: str | None = Query(None, max_length=100, description="Keyword search over name, type, description, colors, tags"),
    category: str | None = Query(None, max_length=40, description='Garment category, e.g. "hoodie", "t-shirt", "jacket"'),
    size: Literal["XS", "S", "M", "L", "XL", "XXL"] | None = Query(None, description="Only products with this size in stock"),
    max_price: float | None = Query(None, ge=0, description="Maximum price in USD"),
    sort: Literal["name", "price_asc", "price_desc"] = Query("name"),
) -> list[ProductCard]:
    return tools.query_products(q, garment_type=category, max_price=max_price, size_in_stock=size, sort=sort)


@app.get("/api/products/{product_id}", response_model=ProductCard)
def get_product(product_id: str) -> ProductCard:
    card = tools.get_product_card(product_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return card


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, user: UserOut | None = Depends(optional_user)) -> ChatResponse:
    customer = chat_history.load_customer(user.id) if user else None
    # Logged-in shoppers: history comes from the database (the browser's copy is ignored).
    # Guests: history is whatever the browser sends, and nothing is saved.
    history = chat_history.load_agent_history(customer.id) if customer else body.history
    try:
        response = await run_chat(body.message, history, customer, body.page)
    except Exception:
        logger.exception("Chat agent failed")
        raise HTTPException(
            status_code=502,
            detail="Sorry, our shopping assistant is having trouble right now. Please try again in a moment.",
        )
    if customer:
        chat_history.save_exchange(customer.id, body.message, response.reply, response.results)
        response.saved = True
    return response


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(user: UserOut = Depends(current_user)) -> ChatHistoryResponse:
    """The logged-in shopper's saved conversation (most recent 100 messages, oldest first)."""
    return ChatHistoryResponse(messages=chat_history.load_history(user.id))


@app.delete("/api/chat/history")
def delete_chat_history(user: UserOut = Depends(current_user)) -> dict:
    """Start a new chat: delete the logged-in shopper's saved messages."""
    return {"deleted": chat_history.clear_history(user.id)}
