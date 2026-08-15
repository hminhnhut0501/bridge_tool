# Group mapping

Verified mappings from `bot_config`:

| Code | Telegram group |
| --- | --- |
| `PRIME` | `-1003857691232` |
| `BOY` | `-1003835994262` |
| `REAL` | `-1003895162881` |
| `ASIA` | `-1003865232620` |
| `PINK_SPECIAL` | `-1004434723714` |

`COMBO_FULL` maps to all four groups. It is represented in the mapping table as
four rows, not as one arbitrary `group_id`. The expansion migration creates
four child entitlements with target codes `PRIME`, `BOY`, `REAL`, and `ASIA`.
The original `COMBO_FULL` row remains only as an audit parent and is never a
kick target.

`PINK_SPECIAL` is now mapped to `-1004434723714`. Before enabling Pink jobs,
verify that the bot is an administrator with permission to remove members.
