# AEGIS Architecture

## Overview

AEGIS is a local-first autonomous AI agent execution platform. It consists of a
Python backend built with FastAPI and a Next.js frontend.

## Design Principles

1. **Local-first**: Runs on local hardware. No cloud dependencies.
2. **Lightweight**: Minimal dependencies. SQLite for development.
3. **Modular**: Each component is a separate module with a clear interface.
4. **Testable**: Every module has unit tests.

## High-Level Components

### Backend (`backend/`)

- **API**: FastAPI application exposing REST endpoints.
- **Database**: SQLAlchemy ORM. SQLite during development, PostgreSQL later.
- **Tests**: pytest-based unit tests.

### Frontend (`frontend/`)

- **UI**: Next.js application.

### Documentation (`docs/`)

- Design documents, API specs, and guides.

### Benchmarks (`benchmarks/`)

- Performance and benchmarking tests.

### Scripts (`scripts/`)

- Utility and setup scripts.

## Technology Stack

| Layer       | Technology          | Status     |
|-------------|---------------------|------------|
| Backend     | Python 3.14, FastAPI | Complete  |
| ORM         | SQLAlchemy 2.x      | Complete   |
| Database    | SQLite (dev)        | Complete   |
| Frontend    | Next.js             | Planned    |
| Testing     | pytest              | Complete   |

## Backend Modules

- **`app/models/`**: SQLAlchemy ORM models (Task with status, payloads, timestamps).
- **`app/schemas/`**: Pydantic v2 schemas for request/response validation.
- **`app/providers/`**: Provider abstraction (`BaseProvider` ABC) with `MockProvider`
  for development. Real LLM providers (Ollama) plug in later.
- **`app/engine/`**: `ExecutionEngine` orchestrates task lifecycle with transaction
  safety and duplicate execution prevention.
- **`app/routers/`**: FastAPI routers exposing REST endpoints.
- **`app/task.py`**: `TaskStatus` enum (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED).

## Task Lifecycle

```
PENDING --execute--> RUNNING --complete--> COMPLETED
   |            |
   |            +--failure--> FAILED
   |
   +--cancel--> CANCELLED
```

## Future Components

- Agent engine (governance, intelligence beyond execution)
- Real LLM providers (Ollama)
- PostgreSQL migration
- Docker deployment