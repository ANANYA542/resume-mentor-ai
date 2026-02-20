from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Storage:
    root: Path

    @staticmethod
    def default() -> "Storage":
        return Storage(root=Path(".resume_mentor").resolve())

    def _ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "analyses").mkdir(parents=True, exist_ok=True)

    def save_analysis(self, analysis_id: str, payload: dict[str, Any]) -> Path:
        self._ensure()
        path = self.root / "analyses" / f"{analysis_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def list_analyses(self, limit: int = 20) -> list[dict[str, Any]]:
        self._ensure()
        files = sorted((self.root / "analyses").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        out: list[dict[str, Any]] = []
        for p in files[:limit]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                out.append(
                    {
                        "analysis_id": data.get("analysis_id") or p.stem,
                        "created_at": data.get("created_at"),
                        "path": str(p),
                    }
                )
            except Exception:
                continue
        return out

    def load_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        self._ensure()
        path = self.root / "analyses" / f"{analysis_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

