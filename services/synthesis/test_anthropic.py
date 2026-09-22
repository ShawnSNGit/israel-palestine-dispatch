#!/usr/bin/env python3
from services.synthesis.anthropic_client import AnthropicClient
import os

if __name__ == '__main__':
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        print('Please set ANTHROPIC_API_KEY in environment to run this test')
        raise SystemExit(1)
    c = AnthropicClient(temperature=0.0, max_tokens=200)
    prompt = "Please summarize: One source says X, another says Y. Provide a one-sentence hedged summary and a list of source ids in JSON."
    out = c.structured_summary(prompt)
    print(out.json())
