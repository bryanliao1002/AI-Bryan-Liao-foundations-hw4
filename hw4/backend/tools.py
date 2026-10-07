"""Database-backed tools for the Campus Customs shopping agent, plus the model connection.

The same query helpers back the public product API in main.py, so the website and
the chatbot always read prices and stock from the same place: data/campus_customs.db.
"""

import json
import math
import os
import re
import sqlite3
from functools import lru_cache

from openai import AsyncOpenAI
from pydantic_ai import RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from db import get_conn
from models import (
    AgentDeps,
    InventoryLookup,
    PriceLookup,
    ProductCard,
    ProductDetailsLookup,
    ProductMatch,
    ProductNotFound,
    ProductSummary,
    SearchResults,
    SimilarProduct,
    SimilarProducts,
    SizeAvailability,
    SizeStock,
    SizeStockLookup,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SEARCH_LIMIT = 30  # max products search_products hands to the agent (and so the max cards shown)
SEARCH_COLUMNS = ["c.name", "c.garment_type", "c.description", "c.colors", "c.search_tags"]


# --- Model connection (gpt-5.6-luna through the Portkey gateway) --------------

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")


def get_model() -> OpenAIChatModel:
    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        api_key="portkey",  # Portkey authenticates with the header below instead.
        default_headers={"x-portkey-api-key": os.environ["PORTKEY_API_KEY"]},
        max_retries=3,
        timeout=60,
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


# --- Query helpers -------------------------------------------------------------


def _search_terms(query: str) -> list[str]:
    """Split a free-text query into lowercase words, trimming simple plurals (hoodies -> hoodie)."""
    terms = []
    for word in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", query.lower()):
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        if len(word) > 1:  # skip fragments like the "t" in "t-shirt"
            terms.append(word)
    return terms


def _sorted_sizes(rows: list[sqlite3.Row]) -> list[SizeStock]:
    sizes = [SizeStock(size=r["size"], quantity=r["quantity"]) for r in rows]
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER))


def _card(row: sqlite3.Row, inventory: list[SizeStock]) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
        image_url=f"/media/{row['image_file_path']}",
        display_image_url=f"/media/display/{row['image_file_path']}",
        price=row["price"],
        total_stock=sum(s.quantity for s in inventory),
        inventory=inventory,
    )


# Shopper words for a category -> text that appears in every matching catalogue.garment_type.
# e.g. "hoodie" must also match "hooded sweatshirt" and "full-zip hooded sweatshirt".
CATEGORY_ALIASES = {
    "hoodie": "hood", "hoody": "hood", "hooded": "hood", "hooded sweatshirt": "hood",
    "tee": "t-shirt", "tshirt": "t-shirt", "t shirt": "t-shirt", "t-shirt": "t-shirt",
    "crew neck": "crewneck", "crewneck sweatshirt": "crewneck",
    "quarter zip": "quarter-zip", "1/4 zip": "quarter-zip", "quarterzip": "quarter-zip",
    "long sleeve": "long-sleeve", "long-sleeve shirt": "long-sleeve",
    "coat": "jacket",
}


def garment_category(text: str) -> str:
    key = text.strip().lower()
    if len(key) > 3 and key.endswith("s") and not key.endswith("ss"):
        key = key[:-1]  # hoodies -> hoodie, jackets -> jacket
    return CATEGORY_ALIASES.get(key, key)


SORT_ORDERS = {
    "name": "c.name",
    "price_asc": "c.price, c.name",
    "price_desc": "c.price DESC, c.name",
}


def query_products(
    query: str | None = None,
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size_in_stock: str | None = None,
    limit: int | None = None,
    sort: str = "name",
) -> list[ProductCard]:
    """Search the catalogue. Every query word must appear in at least one text field.

    sort: "name" (A–Z), "price_asc", or "price_desc" (ties broken by name).
    """
    where: list[str] = []
    params: list[object] = []
    for term in _search_terms(query or ""):
        where.append("(" + " OR ".join(f"lower({col}) LIKE ?" for col in SEARCH_COLUMNS) + ")")
        params += [f"%{term}%"] * len(SEARCH_COLUMNS)
    if garment_type:
        where.append("lower(c.garment_type) LIKE ?")
        params.append(f"%{garment_category(garment_type)}%")
    if color:
        where.append("lower(c.colors) LIKE ?")
        params.append(f"%{color.lower()}%")
    if max_price is not None:
        where.append("c.price <= ?")
        params.append(max_price)
    if size_in_stock:
        where.append("EXISTS (SELECT 1 FROM inventory s WHERE s.product_id = c.product_id AND upper(s.size) = ? AND s.quantity > 0)")
        params.append(size_in_stock.upper())

    sql = "SELECT c.* FROM catalogue c"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + SORT_ORDERS.get(sort, SORT_ORDERS["name"])
    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        ids = [r["product_id"] for r in rows]
        inv: dict[str, list[sqlite3.Row]] = {pid: [] for pid in ids}
        if ids:
            placeholders = ",".join("?" * len(ids))
            for r in conn.execute(f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({placeholders})", ids):
                inv[r["product_id"]].append(r)
    return [_card(r, _sorted_sizes(inv[r["product_id"]])) for r in rows]


def get_product_card(product_id: str) -> ProductCard | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        inv = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    return _card(row, _sorted_sizes(inv))


def get_product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Load cards for the given ids (two queries total), in the given order, skipping unknown ids and duplicates."""
    ids = list(dict.fromkeys(product_ids))
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    with get_conn() as conn:
        rows = {r["product_id"]: r for r in conn.execute(f"SELECT * FROM catalogue WHERE product_id IN ({placeholders})", ids)}
        inv: dict[str, list[sqlite3.Row]] = {pid: [] for pid in rows}
        for r in conn.execute(f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({placeholders})", ids):
            inv[r["product_id"]].append(r)
    return [_card(rows[pid], _sorted_sizes(inv[pid])) for pid in ids if pid in rows]


def list_garment_types() -> dict[str, int]:
    with get_conn() as conn:
        rows = conn.execute("SELECT lower(garment_type) AS t, COUNT(*) AS n FROM catalogue GROUP BY t ORDER BY n DESC").fetchall()
    return {r["t"]: r["n"] for r in rows}


# --- Agent tools (agent.py registers these) ---------------------------------------
# Each tool records the product_ids it returned in ctx.deps.seen_product_ids, so the
# chat route can check that the products the agent shows are ones it actually looked up.


def search_products(
    ctx: RunContext[AgentDeps],
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size_in_stock: str | None = None,
) -> SearchResults:
    """Search the Campus Customs catalogue. Returns every matching product (up to 30) with live price and stock.

    For a category question ("what hoodies do you have?") use garment_type, not query.
    Use query for themes, designs, sports, colleges, or other keywords.

    Args:
        query: Keywords that must all appear in the product's name, description, colors or tags,
            e.g. "bulldog", "hockey", "harvard", "berkeley". Use "" when only filtering by category/color/price.
        garment_type: Optional category filter: "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket",
            "fleece", "long-sleeve". Covers variants (e.g. "hoodie" includes hooded sweatshirts).
        color: Optional color filter, e.g. "navy", "gray", "white".
        max_price: Optional maximum price in USD.
        size_in_stock: Optional size (XS, S, M, L, XL, XXL); only return products with that size in stock.
    """
    size = (normalize_size(size_in_stock) or size_in_stock) if size_in_stock else None
    cards = query_products(query, garment_type, color, max_price, size)
    shown = cards[:SEARCH_LIMIT]
    ctx.deps.seen_product_ids.update(c.product_id for c in shown)
    filters = {"garment_type": garment_type, "color": color, "max_price": max_price, "size_in_stock": size}
    return SearchResults(
        query=query,
        filters={k: v for k, v in filters.items() if v is not None},
        total_matches=len(cards),
        products=[
            ProductSummary(
                product_id=c.product_id,
                name=c.name,
                garment_type=c.garment_type,
                price=c.price,
                colors=c.colors,
                total_stock=c.total_stock,
                description=c.description,
            )
            for c in shown
        ],
        truncated=len(cards) > SEARCH_LIMIT,
    )


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def resolve_product(product: str) -> ProductCard | ProductNotFound:
    """Find one product from a product_id or a product name (exact, then keyword match)."""
    product = product.strip()
    card = get_product_card(product) or get_product_card(_slug(product))
    if card is not None:
        return card

    with get_conn() as conn:
        row = conn.execute("SELECT product_id FROM catalogue WHERE lower(name) = ?", (product.lower(),)).fetchone()
    if row is not None:
        return get_product_card(row["product_id"])  # type: ignore[return-value]

    matches = query_products(product) if product else []
    if len(matches) == 1:
        return matches[0]
    suggestions = [ProductMatch(product_id=m.product_id, name=m.name, price=m.price) for m in matches[:5]]
    message = (
        f"Several products match '{product}'. Ask the shopper which one, or look up one of the suggestions by product_id."
        if suggestions
        else f"No product matches '{product}'. Try search_products with broader keywords."
    )
    return ProductNotFound(query=product, message=message, suggestions=suggestions)


SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "double xl": "XXL", "extra extra large": "XXL",
}


def normalize_size(size: str) -> str | None:
    """Map shopper wording ("medium", "2XL", "extra large") to a catalogue size, or None."""
    return SIZE_ALIASES.get(re.sub(r"\s+", " ", size.strip().lower()))


def _stock_split(card: ProductCard) -> tuple[list[str], list[str]]:
    in_stock = [s.size for s in card.inventory if s.quantity > 0]
    sold_out = [s.size for s in card.inventory if s.quantity == 0]
    return in_stock, sold_out


def get_product_details(ctx: RunContext[AgentDeps], product: str) -> ProductDetailsLookup | ProductNotFound:
    """Look up one product's description, colors, price, and a stock summary from the database.

    Use this when the shopper asks what an item is like, what it's made of / looks like, or wants an overview.

    Args:
        product: The product_id (preferred, e.g. "basic-hoodie-big-yale") or the product's name.
    """
    card = resolve_product(product)
    if isinstance(card, ProductNotFound):
        return card
    ctx.deps.seen_product_ids.add(card.product_id)
    in_stock, sold_out = _stock_split(card)
    return ProductDetailsLookup(
        product_id=card.product_id,
        name=card.name,
        garment_type=card.garment_type,
        description=card.description,
        colors=card.colors,
        price=card.price,
        total_stock=card.total_stock,
        sizes_in_stock=in_stock,
        sold_out_sizes=sold_out,
    )


def get_price(ctx: RunContext[AgentDeps], product: str) -> PriceLookup | ProductNotFound:
    """Look up the exact current price of one product from the database.

    Call this every time the shopper asks how much something costs.

    Args:
        product: The product_id (preferred) or the product's name.
    """
    card = resolve_product(product)
    if isinstance(card, ProductNotFound):
        return card
    ctx.deps.seen_product_ids.add(card.product_id)
    return PriceLookup(
        product_id=card.product_id,
        name=card.name,
        price=card.price,
        price_display=f"${card.price:,.2f}",
    )


def get_inventory(ctx: RunContext[AgentDeps], product: str) -> InventoryLookup | ProductNotFound:
    """Look up the stock quantity of every size (XS–XXL) of one product from the database.

    Call this when the shopper asks which sizes are available, what's sold out, or how many are left overall.

    Args:
        product: The product_id (preferred) or the product's name.
    """
    card = resolve_product(product)
    if isinstance(card, ProductNotFound):
        return card
    ctx.deps.seen_product_ids.add(card.product_id)
    in_stock, sold_out = _stock_split(card)
    return InventoryLookup(
        product_id=card.product_id,
        name=card.name,
        sizes=[SizeAvailability(size=s.size, quantity=s.quantity, in_stock=s.quantity > 0) for s in card.inventory],
        total_stock=card.total_stock,
        sizes_in_stock=in_stock,
        sold_out_sizes=sold_out,
        completely_sold_out=card.total_stock == 0,
    )


def check_size_stock(ctx: RunContext[AgentDeps], product: str, size: str) -> SizeStockLookup | ProductNotFound:
    """Check whether one specific size of one product is in stock, and how many are left, from the database.

    Call this whenever the shopper asks about a particular size ("do you have it in medium?", "is XL available?").

    Args:
        product: The product_id (preferred) or the product's name.
        size: The size the shopper asked about, e.g. "M", "medium", "XL", "2XL".
    """
    card = resolve_product(product)
    if isinstance(card, ProductNotFound):
        return card
    ctx.deps.seen_product_ids.add(card.product_id)
    in_stock, _ = _stock_split(card)
    normalized = normalize_size(size)
    base = dict(product_id=card.product_id, name=card.name, requested_size=size)

    if normalized is None:
        return SizeStockLookup(
            **base, status="invalid_size", size=None, quantity=0, in_stock=False,
            message=f"'{size}' is not a size we carry. Sizes are {', '.join(SIZE_ORDER)}.",
            other_sizes_in_stock=in_stock,
        )

    quantity = next((s.quantity for s in card.inventory if s.size == normalized), 0)
    others = [s for s in in_stock if s != normalized]
    if quantity > 0:
        return SizeStockLookup(
            **base, status="in_stock", size=normalized, quantity=quantity, in_stock=True,
            message=f"{card.name} is in stock in size {normalized}: {quantity} left.",
            other_sizes_in_stock=others,
        )
    return SizeStockLookup(
        **base, status="sold_out", size=normalized, quantity=0, in_stock=False,
        message=f"{card.name} is SOLD OUT in size {normalized} (unavailable)."
        + (f" Other sizes in stock: {', '.join(others)}." if others else " It is sold out in every size."),
        other_sizes_in_stock=others,
    )


# Garment-type text -> category key, checked in order ("short-sleeve crew-neck t-shirt" is a t-shirt).
CATEGORY_KEYS = ["hood", "quarter-zip", "t-shirt", "jacket", "long-sleeve", "crewneck"]
SIMILAR_LIMIT = 6
NAME_STOPWORDS = {"yale", "the", "and", "shirt", "1", "2", "4"}
WHY_SKIP = {"campus customs", "yale merch", "university merch", "college merch", "college apparel", "yale university"}


def category_of(garment_type: str) -> str:
    gt = garment_type.lower()
    return next((key for key in CATEGORY_KEYS if key in gt), gt)


def _features(card: ProductCard) -> set[str]:
    """Design features used for similarity: search tags plus meaningful name words."""
    words = {w for w in re.findall(r"[a-z0-9]+", card.name.lower()) if w not in NAME_STOPWORDS and len(w) > 2}
    return {t.lower() for t in card.search_tags} | words


@lru_cache(maxsize=1)
def _feature_weights() -> dict[str, float]:
    """Rare features count more: 'fencing' or 'left chest' says more than 'hoodie' or 'kangaroo pocket'."""
    cards = query_products()
    counts: dict[str, int] = {}
    for c in cards:
        for f in _features(c):
            counts[f] = counts.get(f, 0) + 1
    return {f: math.log(len(cards) / n) for f, n in counts.items()}


def find_similar_products(
    ctx: RunContext[AgentDeps],
    product: str,
    size: str | None = None,
    color: str | None = None,
) -> SimilarProducts | ProductNotFound:
    """Find in-stock alternatives to one product: same category, ranked by shared design tags, colors and price.

    Use this when a requested size is sold out, when the shopper wants a color this item doesn't come in,
    or when they ask for "something like this" / "similar items".

    Args:
        product: The product_id (preferred) or name of the product to find alternatives for.
        size: Optional size (XS–XXL, "medium", …). Only alternatives with this size in stock are returned.
        color: Optional color the alternatives must include, e.g. "gray", "white".
    """
    base = resolve_product(product)
    if isinstance(base, ProductNotFound):
        return base
    ctx.deps.seen_product_ids.add(base.product_id)

    norm_size = normalize_size(size) if size else None
    category = category_of(base.garment_type)
    candidates = query_products(garment_type=category, color=color, size_in_stock=norm_size)
    broadened = False
    if color and not [c for c in candidates if c.product_id != base.product_id]:
        # Nothing in this category has that color: look across all categories instead.
        candidates = query_products(color=color, size_in_stock=norm_size)
        broadened = True

    weights = _feature_weights()
    base_features = _features(base)
    base_colors = {c.lower() for c in base.colors}

    def score(c: ProductCard) -> tuple[float, list[str]]:
        shared = sorted(base_features & _features(c), key=lambda f: -weights.get(f, 0))
        shared_colors = base_colors & {x.lower() for x in c.colors}
        points = sum(weights.get(f, 0) for f in shared) + 0.5 * len(shared_colors) + (0.5 if c.price == base.price else 0)
        # Only mention features that are distinctive (rarer than ~1 in 6 products) and not store/brand boilerplate.
        return points, [f for f in shared if weights.get(f, 0) > 1.8 and f not in WHY_SKIP]

    ranked = sorted(
        (c for c in candidates if c.product_id != base.product_id and c.total_stock > 0),
        key=lambda c: (-score(c)[0], c.name),
    )[:SIMILAR_LIMIT]

    results = []
    for c in ranked:
        shared = score(c)[1]
        qty = next((s.quantity for s in c.inventory if s.size == norm_size), None) if norm_size else None
        why = ["same category" if not broadened else c.garment_type]
        if shared:
            why.append("also " + ", ".join(shared[:3]))
        if qty is not None:
            why.append(f"{qty} left in {norm_size}")
        results.append(
            SimilarProduct(
                product_id=c.product_id, name=c.name, garment_type=c.garment_type, price=c.price,
                colors=c.colors, total_stock=c.total_stock, size_quantity=qty, why="; ".join(why),
            )
        )
    ctx.deps.seen_product_ids.update(r.product_id for r in results)

    if results:
        message = f"{len(results)} alternatives to {base.name}" + (f" with {norm_size} in stock" if norm_size else "")
        if broadened:
            message += f". No {category} comes in {color}, so these are other items that include {color}"
    else:
        message = f"No in-stock alternatives to {base.name} match those requirements"
    return SimilarProducts(
        base_product_id=base.product_id, base_name=base.name, category=category,
        size=norm_size, color=color, products=results, message=message + ".",
    )


def list_categories() -> dict[str, int]:
    """List every garment type in the catalogue with how many products each has."""
    return list_garment_types()
