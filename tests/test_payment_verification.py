import copy

import pytest

from shared.backend.payment_verification import ExpectedCheckout, PaymentVerificationError, verify_paid_checkout


@pytest.fixture
def paid():
    return {"id": "cs_test_123", "mode": "payment", "status": "complete", "payment_status": "paid",
            "livemode": False, "amount_total": 999, "currency": "usd", "metadata": {"order_id": "order-123"}}


@pytest.fixture
def expected():
    return ExpectedCheckout(session_id="cs_test_123", order_id="order-123", livemode=False)


def test_accepts_paid_server_retrieved_session_matching_order(paid, expected):
    assert verify_paid_checkout(paid, expected) is None


@pytest.mark.parametrize("field,value", [
    ("id", "cs_test_other"), ("mode", "subscription"), ("status", "open"),
    ("payment_status", "unpaid"), ("payment_status", "no_payment_required"),
    ("livemode", True), ("livemode", 0), ("amount_total", 0),
    ("amount_total", 998), ("amount_total", True), ("currency", "sgd"),
    ("metadata", {"order_id": "other"}), ("metadata", None),
])
def test_rejects_session_that_does_not_match_paid_order(paid, expected, field, value):
    changed = copy.deepcopy(paid)
    changed[field] = value
    with pytest.raises(PaymentVerificationError):
        verify_paid_checkout(changed, expected)


def test_rejects_empty_order_or_session_id(paid):
    with pytest.raises(PaymentVerificationError):
        verify_paid_checkout(paid, ExpectedCheckout(session_id="", order_id="order-123", livemode=False))
