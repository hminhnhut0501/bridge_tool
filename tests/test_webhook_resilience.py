import web_backend


def test_webhook_timeout_is_transient_runtime_error():
    assert web_backend.webhook_runtime_error_is_transient("HTTP Client says - Request timeout error")
    assert web_backend.webhook_runtime_error_is_transient("server disconnected")
    assert not web_backend.webhook_runtime_error_is_transient("Bad Request: invalid webhook URL")


def test_empty_webhook_info_keeps_admin_response_shape():
    info = web_backend.empty_webhook_info("timeout")

    assert info["url"] == ""
    assert info["pending_update_count"] == 0
    assert info["last_error_message"] == "timeout"
    assert web_backend.webhook_problem_reason(None, "https://hangcuvip.onrender.com/webhook") == "unavailable"
