# Phase 7: Supabase production adapter

The worker uses `SupabaseKickJobAdapter` for persistence. Claiming is an RPC
with `FOR UPDATE SKIP LOCKED`, so two worker invocations cannot claim the same
job at the same time.

The RPC clamps the batch to 50 and expires locks after 10 minutes. The adapter
does not contain kick policy; it only claims and updates jobs.

Before deployment, apply the RPC migration and test two concurrent workers in
a staging database.
