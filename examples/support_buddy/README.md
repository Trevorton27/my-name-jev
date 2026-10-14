# Support Buddy X9000 Integration Example

Demonstrates JevOps evaluation for a variety of AI agent actions in a support automation workflow.

## Scenarios

1. **Start Devin Session** - Begin an investigation
2. **Create PR** - Submit a code change
3. **Send Customer Response** - Reply to a customer
4. **Escalate Incident** - Route to a specialized team
5. **Retry Investigation** - Re-investigate with broader scope

## Run

```bash
# Start JevOps API
make dev

# Run all scenarios
cd examples/support_buddy
python integration.py
```
