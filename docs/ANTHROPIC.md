# Anthropic integration

This adds a robust Anthropic client for synthesis-service with:
- retries and exponential backoff
- disk cache for prompt results
- schema validation with pydantic
- simple audit logging (writes small audit JSON files to /tmp)

What you must do to use it
1) Save your Anthropic API key in the repository secrets: Settings → Secrets → Actions → ANTHROPIC_API_KEY
2) Install the Python dependencies listed in services/synthesis/requirements.txt
3) Call services.synthesis.anthropic_client.AnthropicClient from your synthesis pipeline

Testing
- There is a GitHub Actions workflow .github/workflows/test-anthropic.yml you can run manually (or via workflow_dispatch) to verify the client works with your secret.
