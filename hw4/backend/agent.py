"""Campus Customs shopping agent: PydanticAI setup and wiring.

- System prompt: prompts/prompt.md (read once at import)
- Model: gpt-5.6-luna via the Portkey gateway (tools.get_model)
- Tools: database lookups defined in tools.py
- Deps: AgentDeps (logged-in customer + verified page context), turned into extra instructions
- Output: ShopAssistantReply (reply text + product_ids to show as cards)
- Every run is logged step by step to output/audit_trail.json (audit.py)
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from uuid import uuid4

from pydantic_ai import Agent, ModelRetry, RunContext, capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.usage import UsageLimits

import audit
import tools
from models import (
    AgentDeps,
    ChatResponse,
    ChatTurn,
    CustomerContext,
    PageContext,
    ProductResults,
    ShopAssistantReply,
)

logger = logging.getLogger("campus_customs.agent")

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_FILE = BACKEND_DIR / "prompts" / "prompt.md"

agent = Agent(
    tools.get_model(),
    deps_type=AgentDeps,
    output_type=ShopAssistantReply,
    instructions=PROMPT_FILE.read_text(),
    tools=[
        tools.search_products,
        tools.get_product_details,
        tools.get_price,
        tools.get_inventory,
        tools.check_size_stock,
        tools.find_similar_products,
        tools.list_categories,
    ],
    retries=2,  # per tool / output: how often a ModelRetry may send the model back to fix a call or answer
)

# Loop limits for one chat turn. A normal turn uses 2–4 model requests (tool calls, then the
# answer); these caps stop a confused model from looping and running up cost.
MAX_MODEL_REQUESTS = 8
MAX_TOOL_CALLS = 12
USAGE_LIMITS = UsageLimits(request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS)


# --- Reply check (output validator) -----------------------------------------------
# Runs on every final answer before it reaches the shopper. A ModelRetry sends the
# problem back to the model, which must fix its answer (up to `retries` times).

PRICE_RE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RE = re.compile(r"pbkdf2_sha256\$|password_hash|portkey|api[_ -]?key\s*[:=]|sk-[A-Za-z0-9]{16,}", re.IGNORECASE)


def dollar_amounts(text: str) -> set[float]:
    return {round(float(a.replace(",", "")), 2) for a in PRICE_RE.findall(text)}


@agent.output_validator
def check_reply(ctx: RunContext[AgentDeps], output: ShopAssistantReply) -> ShopAssistantReply:
    reply = output.reply
    deps = ctx.deps

    # Privacy: no one else's email, and nothing that looks like a credential.
    own_email = deps.customer.email.lower() if deps.customer else None
    others = sorted({e for e in EMAIL_RE.findall(reply) if e.lower() != own_email})
    if others:
        logger.warning("Reply check: blocked email(s) %s", others)
        raise ModelRetry(
            f"Your reply contains the email address(es) {', '.join(others)}. Never share email addresses other than "
            "the logged-in customer's own (and only when they ask about their account). Rewrite the reply without them."
        )
    if SECRET_RE.search(reply):
        logger.warning("Reply check: blocked credential-like text")
        raise ModelRetry("Your reply mentions credentials or internal system details. Rewrite it without them.")

    # Prices: every $ amount must be a real catalogue price of a product looked up this turn,
    # or an amount the shopper typed themselves ("under $60").
    amounts = dollar_amounts(reply)
    real_prices: set[float] = set()
    if amounts:
        real_prices = {round(c.price, 2) for c in tools.get_product_cards(list(deps.seen_product_ids))}
        unverified = amounts - real_prices - dollar_amounts(deps.user_message)
        if unverified:
            shown = ", ".join(f"${a:,.2f}" for a in sorted(unverified))
            logger.warning("Reply check: unverified price(s) %s", shown)
            raise ModelRetry(
                f"Your reply mentions {shown}, which doesn't match the price of any product you looked up with the "
                "tools in this turn. Look the price up now (get_price or get_product_details) and quote only exact "
                "prices from tool results."
            )
    deps.verified_prices = len(amounts & real_prices)  # product prices confirmed against the DB
    return output


# --- Per-request context (added to the system prompt on every run) -------------------

PAGE_NAMES = {
    "home": "the Home page",
    "products": "the Products (catalogue) page",
    "product_detail": "a product detail page",
    "about": "the About Us page",
    "login": "the Log in page",
    "signup": "the Create account page",
    "other": "a page on the site",
}


@agent.instructions
def customer_context(ctx: RunContext[AgentDeps]) -> str:
    c = ctx.deps.customer
    if c is None:
        return (
            "## Current customer\nThe shopper is a **guest** (not logged in). You don't know their name or email, "
            "and this chat is not saved. If they want their chat remembered, they can log in or create an account."
        )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    return (
        "## Current customer\n"
        "The shopper is logged in. Their chat is saved to their account, and the earlier messages in this "
        f"conversation may be from previous visits. Each earlier message starts with its send time "
        f"(\"[sent … UTC]\"); it is now {now} UTC. Never add such a timestamp to your own replies.\n"
        f"- Name: {c.name} (first name: {c.first_name}, last name: {c.last_name})\n"
        f"- Email: {c.email}\n"
        f"- Customer since: {c.member_since}"
    )


@agent.instructions
def page_context(ctx: RunContext[AgentDeps]) -> str:
    deps = ctx.deps
    page = deps.page
    if page is None:
        return "## Current page\nUnknown."
    lines = ["## Current page", f"The shopper is on {PAGE_NAMES[page.page_type]} (`{page.path}`)."]

    p = deps.current_product
    if p is not None:
        lines.append(
            f'They are viewing the product page for **{p.name}** (product_id: "{p.product_id}"; '
            f"{p.garment_type}; colors on the item: {', '.join(p.colors)}). When they say \"this\", \"it\", "
            '"this one" or "this item", they mean this product unless the conversation clearly points elsewhere. '
            "Use the tools for its price and stock."
        )
    elif page.product_id:
        lines.append(f'The URL refers to an unknown product id "{page.product_id}" (not in the catalogue).')

    if page.page_type == "products" and page.search_query:
        lines.append(f"The Products page search box contains: {json.dumps(page.search_query)}.")

    if deps.shown_products:
        title = json.dumps(page.shown_results_title or "Products")
        names = "; ".join(f'{s.name} ("{s.product_id}")' for s in deps.shown_products[:30])
        lines.append(
            f"The assistant product cards on the page are titled {title} and show: {names}. "
            '"These" or "the ones on the page" most likely means these products.'
        )
    return "\n".join(lines)


def to_model_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Convert chat history into PydanticAI messages.

    Saved messages carry their send time, so the agent can tell an earlier visit from today.
    """
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            content = f"[sent {turn.created_at} UTC] {turn.content}" if turn.created_at else turn.content
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


FILTERED_REPLY = (
    "Sorry, I can't help with that request. I'm here to help you find Campus Customs gear. "
    "Ask me about hoodies, crewnecks, tees, sizes, or prices!"
)


LIMIT_REPLY = (
    "That question needed more lookups than I can do in one go. Could you narrow it down, "
    "for example to one product or one size?"
)

UNVERIFIED_REPLY = (
    "Sorry, I couldn't double-check that answer against our store database, so I won't guess. "
    "Could you ask again, maybe naming the specific item?"
)


def is_content_filter_error(exc: Exception) -> bool:
    """Azure's content filter behind Portkey rejects some prompts (e.g. jailbreak attempts) with a 400."""
    return "content_filter" in str(exc) or "content management policy" in str(exc)


def build_deps(customer: CustomerContext | None, page: PageContext | None) -> AgentDeps:
    """Verify the page's product ids against the database before the agent sees them."""
    current = tools.get_product_card(page.product_id) if page and page.product_id else None
    shown = tools.get_product_cards(page.shown_product_ids) if page else []
    deps = AgentDeps(customer=customer, page=page, current_product=current, shown_products=shown)
    # Products on screen count as "looked up", so the agent may show them as cards again.
    deps.seen_product_ids.update(p.product_id for p in [*shown, *([current] if current else [])])
    return deps


async def run_chat(
    message: str,
    history: list[ChatTurn],
    customer: CustomerContext | None = None,
    page: PageContext | None = None,
) -> ChatResponse:
    deps = build_deps(customer, page)
    deps.user_message = message
    model_history = to_model_history(history)
    audit_info = dict(
        run_id=uuid4().hex[:12],
        user=f"user:{customer.id}" if customer else "guest",
        page=page.path if page else None,
        message=message,
    )

    # capture_run_messages keeps the loop's messages even when the run fails, so every
    # outcome (answer, limit hit, content filter, rejected reply) lands in the audit trail.
    with capture_run_messages() as messages:
        try:
            result = await agent.run(message, deps=deps, message_history=model_history, usage_limits=USAGE_LIMITS)
        except UsageLimitExceeded as exc:
            logger.warning("Agent loop limit hit for message %r: %s", message, exc)
            audit.record_run(messages[len(model_history):], outcome="usage_limit", error=str(exc), **audit_info)
            return ChatResponse(reply=LIMIT_REPLY)
        except UnexpectedModelBehavior as exc:
            # The reply kept failing the reply check: better to say so than show unverified info.
            logger.warning("Reply check failed after retries for message %r", message)
            audit.record_run(messages[len(model_history):], outcome="reply_check_failed", error=str(exc), **audit_info)
            return ChatResponse(reply=UNVERIFIED_REPLY)
        except Exception as exc:
            if is_content_filter_error(exc) or is_content_filter_error(exc.__cause__ or exc):
                audit.record_run(messages[len(model_history):], outcome="content_filter",
                                 error="prompt blocked by the provider's content filter", **audit_info)
                return ChatResponse(reply=FILTERED_REPLY)
            audit.record_run(messages[len(model_history):], outcome="error", error=repr(exc), **audit_info)
            raise
    output = result.output
    audit.record_run(result.new_messages(), outcome="final_result", output=output, **audit_info)

    return ChatResponse(
        reply=output.reply, results=build_results(output, deps), verified_prices=deps.verified_prices
    )


def build_results(output: ShopAssistantReply, deps: AgentDeps) -> ProductResults | None:
    """Turn the agent's product_ids into the product cards the front end renders.

    Cards are rebuilt from the database, so the prices/stock shown on the page can never
    be ones the model made up. Prefer products the tools returned this turn; fall back to
    the agent's ids (e.g. a product from earlier in the chat). Unknown ids are dropped.
    """
    picked = [pid for pid in output.product_ids if pid in deps.seen_product_ids] or output.product_ids
    cards = tools.get_product_cards(picked[: tools.SEARCH_LIMIT])
    if not cards:
        return None
    title = output.results_title or ("Recommended for you" if len(cards) > 1 else cards[0].name)
    return ProductResults(title=title, total=len(cards), products=cards)
