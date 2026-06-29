# Support Inbox schema repair

Run this file when Supabase already has old/partial support tables and the bot shows errors like:

- `Could not find the 'last_message_at' column of 'support_tickets' in the schema cache`
- `relation "public.support_messages" does not exist`
- `column "manager_topic_thread_id" does not exist`

Repair migration:

- `/Users/hminhnhut/prive_bot/supabase/2026-06-29-repair-support-inbox-schema.sql`

Recommended order in Supabase SQL Editor:

1. Run `/Users/hminhnhut/prive_bot/supabase/2026-06-29-repair-support-inbox-schema.sql`
2. Wait until it finishes successfully
3. Redeploy or restart the backend once
4. Open CPAdmin and test one support case again

What this repair does:

- Creates `support_tickets` and `support_messages` if missing
- Adds missing columns like `last_message_at`, `manager_topic_thread_id`, `manager_topic_name`
- Restores defaults, indexes, trigger `touch_updated_at`, RLS policies
- Reloads PostgREST schema cache with `notify pgrst, 'reload schema'`

Notes:

- The script is idempotent: running it again is safe for normal cases.
- It does not delete existing support data.
