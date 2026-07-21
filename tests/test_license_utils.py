from license_utils import load_license_plan_mapping


class _FakeDb:
    def __init__(self, config):
        self.config = config

    def get_config(self, key, default=""):
        return self.config.get(key, default)


def test_load_license_plan_mapping_uses_config_json():
    db = _FakeDb(
        {
            "LICENSE_PLAN_MAPPING_JSON": '{"VIP_PLUS":{"groups":["group_x","group_y"],"duration_days":45,"allow_renew":false}}'
        }
    )

    mapping = load_license_plan_mapping(db)

    assert mapping["VIP_PLUS"].groups == ("group_x", "group_y")
    assert mapping["VIP_PLUS"].duration_days == 45
    assert mapping["VIP_PLUS"].allow_renew is False


def test_load_license_plan_mapping_keeps_defaults():
    mapping = load_license_plan_mapping(_FakeDb({}))

    assert "VIP_BASIC" in mapping
    assert mapping["VIP_BASIC"].groups == ("group_a",)
