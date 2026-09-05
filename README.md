# Israel-Palestine Dispatch

This repository collects dispatches, summaries, and sources related to the Israel–Palestine conflict. The goal of the "topline" improvements is to make this project suitable for legal, press, and expert use by improving provenance, quality control, developer tooling, and contribution workflows.

This branch now includes the "STEMpathize" pipeline: automatic daily snapshots of cited sources, a STEMpathize Digest that synthesizes conflicts with empathy-aware hedging, and machine-readable digests for reproducible analysis.

Key improvements provided in this branch:
- Clear contribution guidelines and code of conduct
- Automated CI for link-checking, linting, and tests
- Provenance and citation guidance for each dispatch
- Security reporting instructions and license
- Simple utilities for checking broken links and validating metadata
- STEMpathize autoupdate: daily snapshots, conflict detection, and empathy-aware hedging

Audience
- Legal teams and press organizations who need reliable provenance and citation metadata
- Researchers who need structured exports (JSON/CSV)
- Contributors who want to improve content and tools

Quickstart
1. Clone the repo
   git clone https://github.com/ShawnSNGit/israel-palestine-dispatch.git
   cd israel-palestine-dispatch

2. Run the autoupdate & digest locally (requires Python 3.8+)
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   python scripts/auto_update.py
   python scripts/generate_digest.py

3. Run tests (if present)
   pytest -q

How to cite a dispatch
- Each dispatch should include a metadata header with: title, authors, date_published, sources (list with URLs), confidence_level, summary.
- See docs/PROVENANCE.md for schema and a validation tool.

Contributing
- See CONTRIBUTING.md for PR workflow, branch naming, tests, and review expectations.

License
- This repository is licensed under the MIT License — see LICENSE for details.
