# Security

## Authentication
- API key-based authentication with prefix lookup and SHA-256 hashed secrets
- Pepper-based key verification prevents rainbow table attacks

## Authorization
- Multi-tenant isolation: every query is scoped to `org_id`
- Cross-tenant access returns 404 (not 403, to prevent org enumeration)

## Request Security
- Request size limit (default 1MB) prevents denial-of-service via large payloads
- Rate limiting (sliding window, default 60 req/min) prevents abuse
- CORS allowlist restricts cross-origin requests

## Response Security
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cache-Control: no-store`

## Policy Engine Safety
- Expression evaluator uses AST parsing with a strict whitelist
- Blocked: function calls, imports, lambdas, dunder access, eval/exec
- Policies cannot execute arbitrary code

## Logging
- Structured logging via structlog
- Secrets redacted from log output
- Correlation IDs for request tracing

## Provider Failure Policy
- Provider failures never silently convert to ALLOW
- Failure reason is always persisted
