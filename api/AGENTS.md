# API KNOWLEDGE BASE

**Generated:** 2026-07-31
**Branch:** main
**Commit:**

> **Agent Instructions**
> This file is a living knowledge base. If you find outdated or missing information while working, update this file before finishing. Only document project-specific deviations, not generic best practices. Keep sections telegraphic and concrete.

## OVERVIEW

Python 3.14 FastAPI backend using Strawberry GraphQL, and `uv` for dependencies.

## STRUCTURE

```
api/
├── main.py                 # Thin entry wrapper
├── pyproject.toml          # uv deps, ruff, ty
├── Dockerfile.dev          # debugpy on port 5678
├── Dockerfile.prod
└── src/
    ├── __init__.py         # FastAPI app, lifespan, CORS, /graphql router
    ├── route/              # GraphQL schema
    │   ├── __init__.py     # AppContext, create_schema(), create_context()
    │   ├── mutate/         # Create/Update/Delete types
    │   ├── query/          # Display types
    │   └── resolve/        # Field resolver wrappers
```

## CONVENTIONS

- **Entry:** `main.py` imports `app` from `src/__init__.py`. Uvicorn runs `main:app` on port 5000.
- **Dependencies:** `uv sync` / `uv sync --frozen`. Run `uvx ruff check --fix`, `uvx ruff format`, and `uvx ty check` from `api/`.
- **GraphQL merging:** `strawberry.tools.merge_types` merges all mutation types into `MutationSchema` and all query types into `QuerySchema` in `route/{mutate,query}/__init__.py`. Resolve types are imported directly, not merged.
- **Naming:**
  - Mutations: `Create<Entity>Type` / `Update<Entity>Type` / `Delete<Entity>Type`, method `create_<entity>` in `mutate/<entity>/create_<entity>.py`
  - Queries: `Display<Entity>Type` with nested `Display<Entity>Fields`, method `display_<entity>` in `query/display_<entity>.py`
  - Resolves: `<Entity>` in `resolve/<entity>.py`

## ANTI-PATTERNS

- **Fat FastAPI routes:** Keep FastAPI routes minimal; logic lives in GraphQL resolvers.

## COMMANDS

```bash
# From repo root
bun run format             # prettier + ruff
bun run typecheck          # tsc/eslint + ty
```

## NOTES

- `AppContext` is shared across requests via `create_context()`; auth is resolved lazily on first access.
