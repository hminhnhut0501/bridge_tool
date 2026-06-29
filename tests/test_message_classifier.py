from message_classifier_utils import classify_message_text


def test_classifier_detects_activation_payload():
    result = classify_message_text("/start act_SUP2026ABC")
    assert result["kind"] == "activation"
    assert result["code"] == "SUP2026ABC"


def test_classifier_detects_coupon_prefix():
    result = classify_message_text("HANGCU_DEMO123", coupon_prefixes=["HANGCU_"])
    assert result["kind"] == "coupon"
    assert result["code"] == "HANGCU_DEMO123"


def test_classifier_detects_hidden_code(monkeypatch):
    monkeypatch.setattr("message_classifier_utils.get_hidden_code", lambda code: {"code": code} if code == "HIDEVIP" else None)
    result = classify_message_text("HIDEVIP")
    assert result["kind"] == "hidden"
    assert result["code"] == "HIDEVIP"


def test_classifier_keeps_plain_text_as_support(monkeypatch):
    monkeypatch.setattr("message_classifier_utils.get_hidden_code", lambda code: None)
    result = classify_message_text("Xin chào admin")
    assert result["kind"] == "support"
    assert result["reason"] == "plain_text"
