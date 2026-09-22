# Makefile: common developer commands
.PHONY: test lint build

test:
	@echo "No centralized tests yet; run service-specific tests"

lint:
	@echo "Run linters in each service folder (black/flake8 for python)"

build-ingest:
	docker build -t israel-dispatch-ingest -f services/ingest/Dockerfile services/ingest
