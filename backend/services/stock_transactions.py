"""
Stock fulfillment helpers — atomic approve flow.

MongoDB multi-document transactions (replica set / Atlas) let us group:
  1. Claim order (pending → confirmed)
  2. Conditional stock decrement per line item
  3. stock_movements audit rows

If any step fails, the whole transaction aborts (or we compensate when transactions
are disabled, e.g. local dev / pytest fake DB).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from pymongo.client_session import ClientSession

from core.db import client

T = TypeVar("T")

def run_optional_transaction(
    *,
    enabled: bool,
    operation: Callable[[ClientSession | None], T],
) -> T:
    if not enabled:
        return operation(None)

    with client.start_session() as session:
        with session.start_transaction():
            return operation(session)
