from web_reconciliation import _paypal_amount_minor


def test_paypal_reconciliation_converts_one_dollar_to_cents():
    assert _paypal_amount_minor({"amount": 1}) == 100


def test_paypal_reconciliation_converts_decimal_dollar_amounts():
    assert _paypal_amount_minor({"amount": "5.90"}) == 590
    assert _paypal_amount_minor({"amount": "19.90"}) == 1990


def test_paypal_reconciliation_invalid_amount_is_zero():
    assert _paypal_amount_minor({"amount": "not-a-number"}) == 0
