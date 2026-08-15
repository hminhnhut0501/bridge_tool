# Phase F: Read-only canary

The canary reads due kick jobs, resolves newer entitlements, and reads
Telegram membership. It never calls `kick()` and never updates job state.

Actions:

- `WOULD_KICK`: expired verified entitlement and member is present;
- `RETAINED`: newer active entitlement exists;
- `ALREADY_ABSENT`: member is not in the group;
- `REVIEW`: incomplete data or unknown membership.

Run at least three cycles and manually inspect samples from each non-empty
action before enabling mutation.
