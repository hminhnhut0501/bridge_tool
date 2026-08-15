# Step 1: Order Lifecycle Normalization

Before changing kick behavior, audit order status and expiry consistency. The
audit is read-only and reports PAID orders already past expiry, EXPIRED orders
with future expiry, lifetime orders, missing expiry, unknown status, and
missing canonical family.

```bash
python3.11 -m scripts.order_lifecycle_audit \
  --output /tmp/order-lifecycle-audit.json
```

No status or expiry is changed automatically. Each issue category must be
reviewed before the next normalization step.
