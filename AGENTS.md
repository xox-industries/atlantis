# PROJECT KNOWLEDGE BASE

**Generated:** 2026-07-31
**Branch:** main
**Commit:**

> **Agent Instructions**
> This file is a living knowledge base. If you find outdated or missing information while working, update this file before finishing. Only document project-specific deviations, not generic best practices. Keep sections telegraphic and concrete. After any refactor that changes structure, conventions, or commands, renew the relevant sections.

## OVERVIEW

Atlantis is a Python 3.14/FastAPI backend connected by Strawberry GraphQL. It is a loose monorepo: no Bun or uv workspaces; root `package.json` only orchestrates cross-project scripts.

## STRUCTURE

```
.
├── api/          # Python 3.14 FastAPI backend (Strawberry GraphQL)
├── .github/      # Production deploy workflows
└── package.json  # Root orchestration scripts
```

## WHERE TO LOOK

| Task           | Location         | Notes                                              |
| -------------- | ---------------- | -------------------------------------------------- |
| API entry      | `api/main.py`    | Thin wrapper; real app in `api/src/__init__.py`    |
| GraphQL schema | `api/src/route/` | `mutate/`, `query/`, `resolve/` strictly separated |

## CONVENTIONS

- **No workspace tooling:** Root `package.json` has no `workspaces`; `api/pyproject.toml` sets `[tool.uv.workspace] members = []`. Use `bun` for web/root, `uv` for API.
- **GraphQL-first:** CLI and backend communicate only through GraphQL. Web uses a generated typed SDK (`gqlClient.ATL_*()`), not Apollo React hooks.
- **Strict typing:** TypeScript `strict` mode on CLI; Python 3.14 annotations mandatory in API; `ty` checks API.
- **API route separation:** `mutate/` (state changes), `query/` (reads), `resolve/` (field wrapping) must not be mixed.
- **Web GraphQL naming:** Operations follow `ATL_<PascalCasePath>_<OperationName>`; every `.tsx` using GraphQL has a same-named `.graphql` file.

## ANTI-PATTERNS (THIS PROJECT)

- **Starting or stopping servers:** Agents must never run `bun run dev`, `bun run dev:down`, or any docker command that starts/stops containers. Services are expected to be running; if a service is down, proceed without server validation.
- **Mixing route concerns:** Keep `mutate`, `query`, and `resolve` strictly separated in `api/src/route/`.
- **Missing type hints:** Python 3.14 annotations are required everywhere.

## COMMANDS

```bash
# After any code change — run in this order
bun run format      # Prettier (web) + ruff (api)
bun run typecheck   # tsc + eslint (web); ty (api)

# After changing GraphQL operations (requires API already running)
bun run cli:codegen # hits http://127.0.0.1:5000/graphql

# User-only lifecycle — agents must NOT run these
bun run dev             # starts docker compose --watch
bun run dev:down        # stops containers
bun run dev:clean       # wipes node_modules/.venv/.next (uses sudo for .next)
bun run dev:install     # fresh bun + uv install
```

## NOTES

- **Agents never start/stop servers.** If a service is not running, proceed without server-side validation.
- Access running services by container name: `atlantis-api`.
- `bun run web:codegen` needs a running API.
- There are **no tests** configured in web or API, and CI does not run tests.
- CI deploys via Tailscale + Docker; it skips `format` and `typecheck`. Production deploys on GitHub releases (`.github/workflows/production.deploy.yml`).
  - Deploy workflows generate `web/public/CHANGELOG.json` from the last 16 git tags and their commits. The dashboard header fetches this file and renders it as JSON.
- **`rtk` is just a tool-calling prefix; no need to care about it.**
