# Architecture Overview

This document describes a production-ready, multi-service architecture for Israel-Palestine Dispatch. The goal is to produce an enterprise-grade, auditable, and defensible platform for legal and press workflows, designed to scale from prototype to a large organization.

Key goals
- Immutable provenance for every piece of evidence
- Reproducible, auditable syntheses with hedging suggestions
- Human-in-the-loop editorial and legal review workflow
- Secure, observable, and scalable microservice architecture

Core services (summary)
- ingest-service: connectors and fetch workers to gather sources and produce snapshots
- provenance-service: snapshot metadata, evidence graph, signature & lineage
- retrieval-service: vectorization, vector DB interface, search API
- synthesis-service: RAG-driven synthesis, hedging generator, conflict detector
- editor-ui: editorial interface for drafting, approval, and publishing

Storage & infra
- Object storage (S3/GCS) for snapshots and signed artifacts
- Postgres for metadata, optional Neo4j for graph analytics
- Vector DB (Milvus / Weaviate / Pinecone)
- Kubernetes (EKS/GKE) for orchestration; Terraform for IaC

Security & compliance
- Signed snapshots with SHA-256, append-only logs, and key management
- Legal review queue and takedown procedures
- RBAC + OIDC for strong access control

Read the other docs for implementation details, deployment, and roadmap.
