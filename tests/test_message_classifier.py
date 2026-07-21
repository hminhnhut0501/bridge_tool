from message_classifier_utils import classify_message_text, classify_private_message


def test_classifier_detects_activation_payload():
    result = classify_message_text("/start act_SUP2026ABC")
    assert result["kind"] == "activation"
    assert result["code"] == "SUP2026ABC"


def test_classifier_detects_license_payload():
    result = classify_message_text("/start lic_LIC-ABC1234")
    assert result["kind"] == "license"
    assert result["code"] == "LIC-ABC1234"


def test_classifier_keeps_coupon_like_text_as_support():
    result = classify_message_text("HANGCU_DEMO123", coupon_prefixes=["HANGCU_"])
    assert result["kind"] == "coupon"
    assert result["reason"] == "coupon_prefix"


def test_classifier_keeps_hidden_code_as_support(monkeypatch):
    monkeypatch.setattr("message_classifier_utils.get_hidden_code", lambda code: {"code": code} if code == "HIDEVIP" else None)
    result = classify_message_text("HIDEVIP")
    assert result["kind"] == "hidden"
    assert result["reason"] == "hidden_match"


def test_classifier_keeps_plain_text_as_support(monkeypatch):
    monkeypatch.setattr("message_classifier_utils.get_hidden_code", lambda code: None)
    result = classify_message_text("Xin chào admin")
    assert result["kind"] == "support"
    assert result["reason"] == "plain_text"


def test_classifier_keeps_media_as_support(monkeypatch):
    monkeypatch.setattr("message_classifier_utils.get_hidden_code", lambda code: None)

    class _Message:
        text = ""
        caption = "Hỗ trợ gấp"
        photo = ["photo"]
        document = None
        video = None
        voice = None
        audio = None
        sticker = None

    result = classify_private_message(_Message())
    assert result["kind"] == "support"
    assert result["reason"] == "plain_text"
