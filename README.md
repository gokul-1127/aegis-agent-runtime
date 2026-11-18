# AEGIS

**Autonomous Execution, Governance and Intelligence System**

A local-first autonomous AI agent execution platform.

## Status

Phase 2 is complete. The task execution engine, MockProvider, task model, and API
endpoints are implemented with 44 passing tests. See
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for current progress.

## Project Structure

```
aegis/
  backend/      # FastAPI application
    app/
      engine/     # Task execution engine
      models/     # SQLAlchemy ORM models
      providers/  # AI provider abstraction (MockProvider)
      routers/    # FastAPI routers
      schemas/    # Pydantic schemas
    tests/        # pytest test suite
  frontend/     # Next.js application
  docs/         # Design and architecture documentation
  benchmarks/   # Performance and benchmarking tests
  scripts/      # Utility and setup scripts
```

## API Endpoints

| Method | Path                          | Description                        |
|--------|-------------------------------|------------------------------------|
| GET    | `/api/v1/health`              | Health check                       |
| POST   | `/api/v1/tasks`               | Create a new task                  |
| GET    | `/api/v1/tasks`               | List tasks (paginated, filterable) |
| GET    | `/api/v1/tasks/{task_id}`     | Get a task by ID                   |
| POST   | `/api/v1/tasks/{task_id}/execute` | Execute a pending task          |
| POST   | `/api/v1/tasks/{task_id}/cancel`  | Cancel a pending task           |
| GET    | `/api/v1/tasks/{task_id}/result`  | Get task execution result       |

## Getting Started

1. Set up the Python backend: see `backend/README.md`
2. Set up the frontend: see `frontend/README.md`

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Decisions](DECISIONS.md)