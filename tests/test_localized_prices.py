from unittest.mock import patch

import sale_utils


def test_usd_price_is_read_from_separate_config_key():
    values = {"PRICE_G1_1M": "99000", "PRICE_G1_1M_USD": "4.99"}
    with patch("sale_utils.db.get_config", side_effect=lambda key, default=0: values.get(key, default)), patch(
        "sale_utils.get_active_sale", return_value=None
    ):
        assert sale_utils.get_price("PRICE_G1_1M", 0, "VND")[0] == 99000
        assert sale_utils.get_price("PRICE_G1_1M", 0, "USD")[0] == 4.99


def test_usd_label_does_not_use_vnd_format():
    with patch("sale_utils.db.get_config", return_value="12.50"), patch("sale_utils.get_active_sale", return_value=None):
        assert sale_utils.format_price_label("PRICE_SVIP_LIFE", 0, "USD") == "$12.50 USD"
