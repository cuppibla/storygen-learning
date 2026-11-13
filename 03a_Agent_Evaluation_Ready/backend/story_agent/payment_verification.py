"""Checkout-session verification primitives; not a checkout or entitlement system.

Only call this on a session fetched directly from Stripe using the server's API
key. A browser-supplied session, success URL, or client-provided price is never
proof of payment. Durable order state, atomic fulfilment, refund handling and
webhook verification remain required before exposing paid generation.
"""
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedCheckout:
    session_id: str
    order_id: str
    livemode: bool
    amount_cents: int = 999
    currency: str = "usd"


class PaymentVerificationError(ValueError):
    """A session is not an exact match for a server-created paid order."""


def verify_paid_checkout(session: Mapping, expected: ExpectedCheckout) -> None:
    """Fail closed unless an authenticated Stripe response matches the order.

    This deliberately does not treat a redirect or an asynchronous pending
    payment as paid. It cannot establish whether a later refund or dispute
    occurred; fulfilment must also consult durable order/payment state.
    """
    if not expected.session_id or not expected.order_id:
        raise PaymentVerificationError("Expected order and session IDs are required.")
    if type(expected.livemode) is not bool or type(expected.amount_cents) is not int or expected.amount_cents <= 0:
        raise PaymentVerificationError("Invalid expected payment configuration.")
    metadata = session.get("metadata")
    if not isinstance(metadata, Mapping):
        raise PaymentVerificationError("Missing checkout metadata.")
    amount = session.get("amount_total")
    valid = (
        session.get("id") == expected.session_id
        and session.get("mode") == "payment"
        and session.get("status") == "complete"
        and session.get("payment_status") == "paid"
        and type(session.get("livemode")) is bool
        and session.get("livemode") is expected.livemode
        and type(amount) is int and amount == expected.amount_cents
        and session.get("currency") == expected.currency
        and metadata.get("order_id") == expected.order_id
    )
    if not valid:
        raise PaymentVerificationError("Checkout session does not match a completed paid order.")
