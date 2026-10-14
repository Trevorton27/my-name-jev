# API Authentication

## API Key Format

```
jvo_{environment}_{prefix}_{secret}
```

- **environment**: `live` or `test`
- **prefix**: 8-character hex string (used for lookup)
- **secret**: 32-character hex string (hashed for verification)

Example: `jvo_test_a1b2c3d4_e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0`

## Usage

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: jvo_test_..." http://localhost:8000/v1/decisions/evaluate
```

## Security

- Only the prefix is stored in plaintext for lookup
- The secret is hashed with SHA-256 + a server-side pepper
- Keys can be scoped to `live` or `test` environments
- Keys can be deactivated without deletion
- All resources are scoped to the organization that owns the key
