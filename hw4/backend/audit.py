"""Append-only audit trail of the agent loop: output/audit_trail.json.

Every chat turn adds one AuditEntry per step of the agent loop:
- each tool the model called (with short argument and result summaries),
- each answer the reply check rejected (output_retry),
- the final answer, or the reason the run stopped early.

The file is a JSON array that only ever grows. Existing entries are never removed or
changed: each write reads the trail, appends the new entries, and atomically swaps the file
in place (so a crash mid-write can't truncate it). If the file can't be parsed, it is left
untouched and new entries go to output/audit_trail.unparsed.jsonl instead.
"""

import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, TypeAdapter
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    ToolReturnPart,
)

from db import ROOT
from models import (
    AuditEntry,
    InventoryLookup,
    PriceLookup,
    ProductDetailsLookup,
    ProductNotFound,
    SearchResults,
    ShopAssistantReply,
    SimilarProducts,
    SizeStockLookup,
)

AUDIT_FILE = ROOT / "output" / "audit_trail.json"
FALLBACK_FILE = ROOT / "output" / "audit_trail.unparsed.jsonl"
SUMMARY_CHARS = 200
PREVIEW_CHARS = 80
OUTPUT_TOOL = "final_result"  # PydanticAI's name for the structured-output tool

AuditTrail = TypeAdapter(list[AuditEntry])
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LONG_NUMBER_RE = re.compile(r"(?:\d[ -]?){7,18}\d")  # 8+ digits, e.g. card or phone numbers
logger = logging.getLogger("campus_customs.audit")
_lock = threading.Lock()


def _scrub(text: str) -> str:
    """Mask personal data before it reaches the log: emails and card/phone-like digit runs."""
    return LONG_NUMBER_RE.sub("[number]", EMAIL_RE.sub("[email]", text))


def _clip(text: str, n: int = SUMMARY_CHARS) -> str:
    text = _scrub(" ".join(str(text).split()))
    return text if len(text) <= n else text[: n - 1] + "…"


def summarize_args(part: ToolCallPart) -> str:
    args = part.args_as_dict()
    if part.tool_name == OUTPUT_TOOL:
        ids = args.get("product_ids") or []
        return _clip(f"reply={args.get('reply', '')!r}; {len(ids)} product card(s); title={args.get('results_title')!r}")
    shown = {k: v for k, v in args.items() if v not in (None, "")}
    return _clip(", ".join(f"{k}={v!r}" for k, v in shown.items()) or "(no arguments)")


def summarize_result(content: object) -> str:
    """One-line description of a tool's return value."""
    if isinstance(content, SearchResults):
        names = ", ".join(p.name for p in content.products[:3])
        return _clip(f"{content.total_matches} match(es), returned {len(content.products)}: {names}")
    if isinstance(content, PriceLookup):
        return _clip(f"{content.name}: {content.price_display}")
    if isinstance(content, SizeStockLookup):
        return _clip(f"{content.status}: {content.message}")
    if isinstance(content, InventoryLookup):
        return _clip(
            f"{content.name}: {content.total_stock} total; in stock {content.sizes_in_stock}; sold out {content.sold_out_sizes}"
        )
    if isinstance(content, ProductDetailsLookup):
        return _clip(f"{content.name}: ${content.price:.2f}, {content.total_stock} in stock, sold out {content.sold_out_sizes}")
    if isinstance(content, SimilarProducts):
        return _clip(f"{content.message} " + ", ".join(p.name for p in content.products[:3]))
    if isinstance(content, ProductNotFound):
        return _clip(f"not_found: {content.message}")
    if isinstance(content, dict):
        return _clip(f"{len(content)} item(s): " + ", ".join(f"{k}={v}" for k, v in list(content.items())[:5]))
    if isinstance(content, BaseModel):
        return _clip(content.model_dump_json())
    return _clip(content)


def build_entries(
    messages: list[ModelMessage],
    *,
    run_id: str,
    user: str,
    page: str | None,
    message: str,
    outcome: str,
    output: ShopAssistantReply | None = None,
    error: str | None = None,
) -> list[AuditEntry]:
    """Turn one run's messages into audit entries, one per tool call / rejected answer / final answer.

    outcome: "final_result" on success, or content_filter / usage_limit / reply_check_failed / error.
    """
    # Results and retries arrive in the *next* request, matched to calls by tool_call_id.
    returns: dict[str, ToolReturnPart] = {}
    retries: dict[str, RetryPromptPart] = {}
    for m in messages:
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, ToolReturnPart):
                    returns[p.tool_call_id] = p
                elif isinstance(p, RetryPromptPart) and p.tool_call_id:
                    retries[p.tool_call_id] = p

    base = dict(
        run_id=run_id,
        user=user,
        page=page,
        message_preview=_clip(message, PREVIEW_CHARS),
    )
    entries: list[AuditEntry] = []
    step = 0
    for m in messages:
        if not isinstance(m, ModelResponse):
            continue
        step += 1
        timestamp = (m.timestamp or datetime.now(timezone.utc)).isoformat(timespec="seconds")
        # The Portkey gateway doesn't always report token counts; store null rather than a misleading 0.
        tokens = (m.usage.total_tokens or None) if m.usage else None
        finish = m.finish_reason
        for part in m.parts:
            if not isinstance(part, ToolCallPart):
                continue
            common = dict(base, timestamp=timestamp, step=step, tool=part.tool_name,
                          args_summary=summarize_args(part), model_finish_reason=finish, tokens=tokens)
            if part.tool_call_id in retries:
                entries.append(AuditEntry(**common, event="output_retry" if part.tool_name == OUTPUT_TOOL else "tool_call",
                                          result_summary=_clip("rejected: " + str(retries[part.tool_call_id].content)),
                                          stop_reason="output_retry" if part.tool_name == OUTPUT_TOOL else "tool_call"))
            elif part.tool_name == OUTPUT_TOOL:
                accepted = output is not None
                summary = (f"answer shown; {len(output.product_ids)} product id(s)" if accepted
                           else "answer not shown (run stopped)")
                entries.append(AuditEntry(**common, event="final_answer", result_summary=summary,
                                          stop_reason="final_result" if accepted else outcome))
            else:
                ret = returns.get(part.tool_call_id)
                entries.append(AuditEntry(**common, event="tool_call",
                                          result_summary=summarize_result(ret.content) if ret else "(no result recorded)",
                                          stop_reason="tool_call"))

    if outcome != "final_result":
        # Record why the loop stopped without a normal answer.
        entries.append(AuditEntry(
            **base, timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"), step=step + 1,
            event="run_error", tool=None, args_summary="", result_summary=_clip(error or outcome),
            stop_reason=outcome,
        ))
    return entries


def append_entries(entries: list[AuditEntry], path: Path | None = None) -> None:
    """Append to the audit trail. Existing entries are never removed or rewritten."""
    if not entries:
        return
    path = path or AUDIT_FILE
    with _lock:
        try:
            existing = AuditTrail.validate_json(path.read_bytes()) if path.exists() and path.stat().st_size else []
        except Exception:
            # Never overwrite a trail we can't read: park the new entries next to it instead.
            logger.error("Audit trail %s is not valid JSON; writing to %s", path, FALLBACK_FILE)
            with FALLBACK_FILE.open("a") as f:
                for e in entries:
                    f.write(e.model_dump_json() + "\n")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_bytes(AuditTrail.dump_json(existing + entries, indent=2))
        tmp.replace(path)  # atomic swap


def record_run(messages: list[ModelMessage], **kwargs) -> None:
    """Build and append a run's entries. Audit problems are logged, never shown to the shopper."""
    try:
        append_entries(build_entries(messages, **kwargs))
    except Exception:
        logger.exception("Could not write audit trail")
