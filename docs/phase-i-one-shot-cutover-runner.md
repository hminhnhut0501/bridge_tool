# Phase I: One-shot cutover runner

The production entrypoint executes one bounded batch and exits. It does not
contain a permanent loop; cron, a platform scheduler, or an external job
runner invokes it again later.

Safety order:

1. kill switch must be on;
2. cutover gate must allow mutation;
3. batch is clamped to five;
4. worker runs once;
5. process exits with its result.

If any guard fails, no Telegram mutation is attempted.
