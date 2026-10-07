"""Customer memory: saving and loading logged-in shoppers' chat history (chat_messages table).

Each message is one row:  user_id, role ("user" | "assistant"), content, products_json, created_at.
For assistant messages, products_json stores the product results that were shown with the reply:
    {"title": "Yale Hoodies", "product_ids": ["basic-hoodie-big-yale", ...]}
Only ids are stored. When history is loaded, cards are rebuilt from the catalogue so prices
and stock are always current. Rows written before this format (a JSON list of product objects)
are still read: their product_ids are used with a generic title.
"""

import json

import tools
from db import get_conn
from models import ChatMessageOut, ChatTurn, CustomerContext, ProductResults

AGENT_HISTORY_MESSAGES = 20  # how many recent messages the agent gets as context
DISPLAY_HISTORY_MESSAGES = 100  # how many recent messages the chat widget shows


def load_customer(user_id: int) -> CustomerContext | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, email, first_name, last_name, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    first, _, last = row["name"].partition(" ")
    return CustomerContext(
        id=row["id"],
        first_name=row["first_name"] or first,
        last_name=row["last_name"] or last,
        name=row["name"],
        email=row["email"],
        member_since=(row["created_at"] or "")[:10],
    )


def _encode_results(results: ProductResults | None) -> str | None:
    if results is None:
        return None
    return json.dumps({"title": results.title, "product_ids": [p.product_id for p in results.products]})


def _decode_results(products_json: str | None) -> ProductResults | None:
    if not products_json:
        return None
    try:
        data = json.loads(products_json)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):  # current format
        title, ids = data.get("title") or "Products", data.get("product_ids") or []
    elif isinstance(data, list):  # older rows: list of full product objects
        title, ids = "Products from this chat", [p.get("product_id") for p in data if isinstance(p, dict)]
    else:
        return None
    cards = tools.get_product_cards([i for i in ids if isinstance(i, str)])
    return ProductResults(title=title, total=len(cards), products=cards) if cards else None


def _recent_rows(user_id: int, limit: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? AND role IN ('user', 'assistant') ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def load_history(user_id: int, limit: int = DISPLAY_HISTORY_MESSAGES) -> list[ChatMessageOut]:
    """Recent messages for the chat widget, oldest first, with product cards rebuilt from the DB."""
    return [
        ChatMessageOut(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            results=_decode_results(r["products_json"]) if r["role"] == "assistant" else None,
            created_at=r["created_at"],
        )
        for r in _recent_rows(user_id, limit)
    ]


def load_agent_history(user_id: int, limit: int = AGENT_HISTORY_MESSAGES) -> list[ChatTurn]:
    """Recent messages as plain turns for the agent's message history."""
    return [ChatTurn(role=r["role"], content=r["content"], created_at=r["created_at"]) for r in _recent_rows(user_id, limit)]


def save_exchange(user_id: int, user_message: str, reply: str, results: ProductResults | None) -> None:
    """Save the shopper's message and the assistant's reply together (one transaction)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, user_message)
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, _encode_results(results)),
        )


def clear_history(user_id: int) -> int:
    """Delete this shopper's saved chat ("New chat"). Returns how many rows were removed."""
    with get_conn() as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount
