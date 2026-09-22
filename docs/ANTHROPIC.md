# Anthropic integration

The synthesis client uses Anthropic's **Messages API** (`/v1/messages`), with:
- retries only for network errors, HTTP 429, and server errors;
- a local TTL cache to avoid repeated requests;
- strict JSON extraction and Pydantic validation;
- no API keys or full prompts written to logs.

Set these environment values:

```text
ANTHROPIC_API_KEY=your-key
ANTHROPIC_MODEL=your-approved-model-name
```

`ANTHROPIC_MODEL` is intentionally configurable because model names change. The
GitHub workflow performs offline checks on every relevant change and performs a
live check only when `ANTHROPIC_API_KEY` is configured as a repository secret.
