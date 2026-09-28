from __future__ import annotations

import asyncio
from pathlib import Path


async def list_directories(base_path: Path, max_depth: int) -> list[str]:
    """Return directory paths relative to ``base_path`` up to ``max_depth`` levels deep.

    ``base_path`` should already be resolved. ``max_depth`` of ``1`` returns only
    immediate subdirectories.
    """
    if max_depth < 1:
        return []

    def _walk() -> list[str]:
        resolved_base = base_path.resolve()
        return [
            str(entry.relative_to(resolved_base))
            for entry in sorted(resolved_base.rglob("*"))
            if entry.is_dir() and len(entry.relative_to(resolved_base).parts) <= max_depth
        ]

    return await asyncio.to_thread(_walk)
