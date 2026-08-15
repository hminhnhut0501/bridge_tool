# Phase J: Legacy freeze

After the new worker cutover, legacy renewal code enters `READ_ONLY` mode.

Legacy code may still be used for:

- audit comparison;
- rollback investigation;
- historical reporting.

Legacy code may not:

- create new kick jobs;
- claim delayed jobs;
- call Telegram kick/mute APIs;
- change entitlement state.

Deletion is intentionally deferred until the new worker has completed a full
observation window without data loss or incorrect kicks.
