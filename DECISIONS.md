# AEGIS Decisions

This file records architectural and implementation decisions.

## Decision 1: Use SQLite for Development

**Date**: 2026-11-18
**Decision**: Use SQLite as the database during development.
**Why**: Limited hardware resources (8 GB RAM). PostgreSQL will be adopted later when
scaling is required.
**Status**: Accepted

## Decision 2: Use MockProvider for LLM

**Date**: 2026-11-18
**Decision**: Implement a MockProvider that simulates LLM responses.
**Why**: Avoid requiring a local LLM during development. This keeps the platform
lightweight and testable without GPU dependencies.
**Status**: Accepted

## Decision 3: FastAPI + SQLAlchemy

**Date**: 2026-11-18
**Decision**: Use FastAPI for the backend and SQLAlchemy 2.x as the ORM.
**Why**: FastAPI provides automatic OpenAPI docs and strong type validation via
Pydantic. SQLAlchemy 2.x is a mature, widely-supported ORM.
**Status**: Accepted

## Decision 4: No Kubernetes

**Date**: 2026-11-18
**Decision**: Do not use Kubernetes for now.
**Why**: Kubernetes is too heavy for the current hardware constraints.
**Status**: Accepted

## Decision 5: Provider Abstraction for LLM Calls

**Date**: 2026-11-18
**Decision**: Abstract all LLM/AI calls behind a `BaseProvider` interface with a
swappable provider implementation (currently `MockProvider`).
**Why**: Keeps the execution engine decoupled from any specific AI backend.
`MockProvider` enables full development and testing without a GPU or local LLM.
Real providers (Ollama, API-based) can be added later without touching engine code.
**Status**: Accepted

## Decision 6: Task Status State Machine

**Date**: 2026-11-18
**Decision**: Enforce a strict task status state machine with PENDING, RUNNING,
COMPLETED, FAILED, and CANCELLED states. A task can only be executed or cancelled
from the PENDING state.
**Why**: Prevents duplicate execution, race conditions, and invalid state
transitions. Combined with row-level transaction locking in the execution engine,
this guarantees exactly-once execution semantics.
**Status**: Accepted