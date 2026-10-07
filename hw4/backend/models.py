"""Pydantic / PydanticAI structured types for the Campus Customs backend and agent."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

# --- Products -----------------------------------------------------------------


class SizeStock(BaseModel):
    size: str = Field(description="One of XS, S, M, L, XL, XXL")
    quantity: int = Field(description="Units in stock for this size (0 = sold out)")


class ProductSummary(BaseModel):
    """Compact product info returned by the search tool (enough for the agent to choose)."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="Price in USD, straight from the catalogue")
    colors: list[str]
    total_stock: int = Field(description="Units in stock across all sizes")
    description: str


class SearchResults(BaseModel):
    """Result of the search_products tool."""

    query: str = Field(description="The keywords that were searched")
    filters: dict[str, str | float] = Field(description="Filters that were applied (category, color, max_price, size)")
    total_matches: int = Field(description="How many catalogue products match in total")
    products: list[ProductSummary] = Field(description="The matching products (up to 30), sorted by name")
    truncated: bool = Field(description="True if there were more matches than returned")


class ProductCard(BaseModel):
    """Everything the frontend needs to render a product card or detail page."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str = Field(description="Original photo, from catalogue.image_file_path")
    display_image_url: str = Field(description="Same photo on the storefront's neutral tile background (images.py)")
    price: float
    total_stock: int
    inventory: list[SizeStock] = Field(default_factory=list)


# --- Lookup tool results (what the agent sees) --------------------------------
# Every lookup echoes product_id + name so the agent can tie the numbers to the
# right product, and stock results carry ready-made in_stock / sold_out fields so
# the agent never has to interpret raw quantities on its own.


class ProductMatch(BaseModel):
    """A lightweight product reference used for suggestions."""

    product_id: str
    name: str
    price: float


class ProductNotFound(BaseModel):
    """Returned by any lookup tool when the product can't be identified unambiguously."""

    status: Literal["not_found"] = "not_found"
    query: str = Field(description="What the agent asked for")
    message: str
    suggestions: list[ProductMatch] = Field(
        default_factory=list, description="Close matches to offer the shopper or look up next"
    )


class ProductDetailsLookup(BaseModel):
    """Result of get_product_details: the full description plus price and a stock summary."""

    status: Literal["found"] = "found"
    product_id: str
    name: str
    garment_type: str
    description: str = Field(description="Catalogue description of the item")
    colors: list[str] = Field(description="Every color on the item (one colorway, not color options)")
    price: float = Field(description="Price in USD from catalogue.price")
    total_stock: int = Field(description="Units in stock across all sizes")
    sizes_in_stock: list[str] = Field(description="Sizes with quantity > 0, smallest first")
    sold_out_sizes: list[str] = Field(description="Sizes with quantity 0")


class PriceLookup(BaseModel):
    """Result of get_price."""

    status: Literal["found"] = "found"
    product_id: str
    name: str
    price: float = Field(description="Price in USD from catalogue.price")
    price_display: str = Field(description='Price formatted for the shopper, e.g. "$68.00"')
    currency: Literal["USD"] = "USD"


class SizeAvailability(SizeStock):
    in_stock: bool = Field(description="True when quantity > 0")


class InventoryLookup(BaseModel):
    """Result of get_inventory: stock for every size of one product."""

    status: Literal["found"] = "found"
    product_id: str
    name: str
    sizes: list[SizeAvailability] = Field(description="All sizes XS→XXL with quantity and in_stock flag")
    total_stock: int
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    completely_sold_out: bool = Field(description="True when every size has quantity 0")


class SizeStockLookup(BaseModel):
    """Result of check_size_stock: availability of one size of one product."""

    status: Literal["in_stock", "sold_out", "invalid_size"]
    product_id: str
    name: str
    requested_size: str = Field(description="The size exactly as it was asked for")
    size: str | None = Field(description="Normalized size (XS, S, M, L, XL, XXL), or null if not a valid size")
    quantity: int = Field(description="Units in stock for this size (0 if sold out or invalid)")
    in_stock: bool
    message: str = Field(description="Plain-English summary the agent can rely on")
    other_sizes_in_stock: list[str] = Field(description="Other sizes of this product that are in stock")


class SimilarProduct(BaseModel):
    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    total_stock: int
    size_quantity: int | None = Field(
        default=None, description="Units in stock in the requested size (only set when a size was requested)"
    )
    why: str = Field(description='Short reason it was picked, e.g. "same category; also bulldog, vintage; 15 left in M"')


class SimilarProducts(BaseModel):
    """Result of find_similar_products: in-stock alternatives to one product."""

    status: Literal["found"] = "found"
    base_product_id: str
    base_name: str
    category: str = Field(description="Category the alternatives were drawn from")
    size: str | None = Field(description="Size the alternatives are guaranteed to have in stock, if one was requested")
    color: str | None = Field(description="Color the alternatives include, if one was requested")
    products: list[SimilarProduct] = Field(description="Best matches first (up to 6). Empty if nothing fits.")
    message: str


# --- Chat API -----------------------------------------------------------------


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    created_at: str | None = Field(default=None, exclude=True)  # set for saved history (UTC), not sent by the browser


class PageContext(BaseModel):
    """What the shopper is looking at, sent by the front end with every chat message.

    Only ids and short strings are accepted; the backend looks product names/details
    up in the database itself, so the page can't inject made-up product info.
    """

    path: str = Field(default="/", max_length=200, description="Current URL path, e.g. /products/basic-hoodie-big-yale")
    page_type: Literal["home", "products", "product_detail", "about", "login", "signup", "other"] = "other"
    product_id: str | None = Field(default=None, max_length=120, description="Product open on a detail page")
    search_query: str | None = Field(default=None, max_length=100, description="Search box text on the Products page")
    shown_results_title: str | None = Field(default=None, max_length=60, description="Heading of the assistant cards on the page")
    shown_product_ids: list[str] = Field(default_factory=list, max_length=30, description="Assistant cards on the page")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    # Only used for guests. For logged-in shoppers the server loads history from the database.
    history: list[ChatTurn] = Field(default_factory=list, max_length=30)
    page: PageContext | None = None


class ProductResults(BaseModel):
    """Products the front end renders as regular product cards on the page."""

    title: str = Field(description='Heading shown above the cards, e.g. "Hoodies"')
    total: int = Field(description="Number of products in this result set")
    products: list[ProductCard]


class ChatResponse(BaseModel):
    """The /api/chat contract: the reply text, plus product results to render (or null)."""

    reply: str
    results: ProductResults | None = None
    saved: bool = Field(default=False, description="True when this exchange was saved to the shopper's chat history")
    verified_prices: int = Field(
        default=0, description="How many $ amounts in the reply were checked against the database (0 = none mentioned)"
    )


class ChatMessageOut(BaseModel):
    """One saved chat message, as returned by GET /api/chat/history."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    results: ProductResults | None = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageOut]


# --- Customer memory ------------------------------------------------------------


class CustomerContext(BaseModel):
    """The logged-in customer, as the agent sees them. Never includes the password hash."""

    id: int
    first_name: str
    last_name: str
    name: str
    email: str
    member_since: str = Field(description="Account creation date (YYYY-MM-DD)")


# --- Agent --------------------------------------------------------------------


class ShopAssistantReply(BaseModel):
    """The agent's structured final answer."""

    reply: str = Field(
        description="The message shown to the shopper. Friendly, concise, Markdown allowed "
        "(bold, short bullet lists). Every price or stock number must come from a tool result."
    )
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=30,
        description="product_id values (from tool results) to display as product cards on the page, "
        "most relevant first. For a browse/search question, include every match the search returned. "
        "For a question about specific items, include just those. Empty if no product is relevant.",
    )
    results_title: str | None = Field(
        default=None,
        max_length=60,
        description='Short heading for the cards, e.g. "Hoodies", "Bulldog crewnecks", "Navy items under $60". '
        "Null when product_ids is empty.",
    )


class AuditEntry(BaseModel):
    """One record in output/audit_trail.json: one step of the agent loop."""

    timestamp: str = Field(description="When the step happened (UTC, ISO 8601)")
    run_id: str = Field(description="Groups the entries of one chat turn")
    step: int = Field(description="Agent-loop iteration: the model response number within the run (1, 2, ...)")
    event: Literal["tool_call", "output_retry", "final_answer", "run_error"]
    tool: str | None = Field(description="Tool the model called (final_result for the structured answer), or null")
    args_summary: str = Field(description="Short summary of the tool arguments (≤ 200 chars)")
    result_summary: str = Field(description="Short summary of what the tool returned, or why it was rejected (≤ 200 chars)")
    stop_reason: str = Field(
        description="Why this step ended: tool_call (loop continues), output_retry (answer rejected, loop continues), "
        "final_result (loop ended with an answer), or how the run stopped early: content_filter, usage_limit, "
        "reply_check_failed, error"
    )
    model_finish_reason: str | None = Field(default=None, description="Raw finish reason reported by the model API")
    user: str = Field(description='"user:<id>" for logged-in shoppers, "guest" otherwise (no names or emails)')
    page: str | None = Field(default=None, description="Page path the shopper was on")
    message_preview: str = Field(description="First 80 chars of the shopper's message, emails and long numbers masked")
    tokens: int | None = Field(default=None, description="Total tokens for this model response, if the gateway reports it")


@dataclass
class AgentDeps:
    """Per-request context passed to the agent and its tools."""

    user_message: str = ""  # this turn's message (amounts the shopper typed are allowed in the reply)
    verified_prices: int = 0  # set by the reply check in agent.py
    customer: CustomerContext | None = None  # None for guests
    page: PageContext | None = None
    current_product: ProductCard | None = None  # page.product_id, verified against the database
    shown_products: list[ProductCard] = field(default_factory=list)  # page.shown_product_ids, verified
    # product_ids the tools returned during this run (used to sanity-check the agent's picks).
    seen_product_ids: set[str] = field(default_factory=set)
