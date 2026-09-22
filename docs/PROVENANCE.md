# Provenance & Citation Guidelines

This project aims to provide clear provenance for each dispatch. Each dispatch file should include a top-level metadata block (YAML or JSON) with the following fields:

- title: string
- authors: list of strings
- date_published: ISO 8601 date
- sources: list of {url, title, type}
- confidence_level: one of [low, medium, high]
- summary: short summary for quick reading

Validation
- Use the provided script scripts/validate_provenance.py to validate metadata and flag missing sources.

Example (YAML frontmatter):
---
title: "Dispatch title"
authors:
  - "Author Name"
date_published: "2024-10-01"
sources:
  - url: "https://example.org/source"
    title: "Source title"
    type: "news"
confidence_level: "medium"
summary: "One-line summary"
---

See scripts/validate_provenance.py for an automated validator.
