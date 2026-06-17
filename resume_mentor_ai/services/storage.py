"""
Local JSON-based version storage for analysis results.

Design decisions
----------------
- Each analysis gets its own file named by analysis_id.
- ``save_analysis()`` will NOT silently overwrite — it raises StorageError
  if the ID already exists (callers should generate unique IDs).
- File writes are atomic via a temp-file + rename pattern.
- List ordering is by ``created_at`` field embedded in JSON (not file mtime).
- Path traversal is prevented by resolving the final path and asserting it
  is strictly inside the analyses directory.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StorageError(RuntimeError):
    """Raised on storage failures (I/O errors, duplicate IDs, etc.)."""


@dataclass(frozen=True)
class Storage:
    root: Path = field(default_factory=lambda: Path(".resume_mentor").resolve())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyses_dir(self) -> Path:
        d = self.root / "analyses"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _path_for(self, analysis_id: str) -> Path:
        """
        Return the resolved file path for *analysis_id*.

        Raises StorageError if the resolved path escapes the analyses directory
        (path traversal protection) or if the ID contains illegal characters.
        """
        # First-pass: reject obviously dangerous characters.
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        if not analysis_id or not all(c in safe_chars for c in analysis_id):
            raise StorageError(
                f"Invalid analysis_id {analysis_id!r}: only alphanumeric, '-', and '_' are allowed."
            )

        analyses_dir = self._analyses_dir().resolve()
        candidate = (analyses_dir / f"{analysis_id}.json").resolve()

        # Second-pass: confirm the resolved path is still inside analyses_dir.
        try:
            candidate.relative_to(analyses_dir)
        except ValueError:
            raise StorageError(
                f"analysis_id {analysis_id!r} resolves outside the storage directory."
            )

        return candidate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def default() -> "Storage":
        return Storage(root=Path(".resume_mentor").resolve())

    def save_analysis(
        self,
        analysis_id: str,
        payload: dict[str, Any],
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Persist *payload* as JSON under *analysis_id*.

        Parameters
        ----------
        overwrite:
            If False (default) and the ID already exists, raise StorageError.
            Set True to explicitly update an existing record.

        Returns
        -------
        Path to the saved file.
        """
        path = self._path_for(analysis_id)
        if path.exists() and not overwrite:
            raise StorageError(
                f"Analysis {analysis_id!r} already exists. "
                "Use overwrite=True to replace it."
            )

        # Atomic write: write to temp file then rename.
        dir_ = path.parent
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".json.tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
                os.replace(tmp_path, path)  # atomic on POSIX and Windows
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as e:
            raise StorageError(f"Failed to save analysis {analysis_id!r}: {e}") from e

        logger.debug("Saved analysis %s → %s", analysis_id, path)
        return path

    def list_analyses(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Return summary records for the most recent *limit* analyses,
        sorted by ``created_at`` descending (newest first).
        """
        analyses_dir = self._analyses_dir()
        records: list[dict[str, Any]] = []

        for p in analyses_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                records.append(
                    {
                        "analysis_id": data.get("analysis_id", p.stem),
                        "created_at": data.get("created_at"),
                        "overall_score": data.get("score", {}).get("overall"),
                        "path": str(p),
                    }
                )
            except Exception:
                logger.warning("Could not read analysis file: %s", p)

        # Sort by created_at (ISO string sorts lexicographically).
        records.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return records[:limit]

    def load_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        """
        Load a previously saved analysis by ID.

        Returns None if not found.
        """
        path = self._path_for(analysis_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise StorageError(f"Failed to load analysis {analysis_id!r}: {e}") from e

    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis by ID.

        Returns True if deleted, False if it did not exist.
        """
        path = self._path_for(analysis_id)
        if not path.exists():
            return False
        path.unlink()
        logger.info("Deleted analysis: %s", analysis_id)
        return True

    def count(self) -> int:
        """Return the total number of stored analyses."""
        return sum(1 for _ in self._analyses_dir().glob("*.json"))