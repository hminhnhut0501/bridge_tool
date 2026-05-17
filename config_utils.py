from database import db


def config_int(key, default, minimum=None, maximum=None):
    try:
        value = int(float(str(db.get_config(key, str(default)) or default).strip()))
    except Exception:
        value = default
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def group_count():
    return config_int("GROUP_COUNT", 20, minimum=1, maximum=100)


def group_numbers():
    return range(1, group_count() + 1)
