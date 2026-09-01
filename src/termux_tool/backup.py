"""Timestamped, path-safe backups and restoration."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Dict, List, Optional

from .errors import SafetyError, ToolError
from .paths import AppPaths, allowed_restore_target, ensure_within
from .storage import ensure_private_dir, write_json


class BackupManager:
    """Owns backups below one private directory and never overwrites them."""

    def __init__(self, paths: AppPaths):
        self.paths = paths
        self.directory = paths.backup_dir
        self.manifest = self.directory / "manifest.json"

    def _records(self) -> List[Dict[str, str]]:
        if not self.manifest.exists():
            return []
        try:
            value = json.loads(self.manifest.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, ValueError):
            return []

    def _save_records(self, records: List[Dict[str, str]]) -> None:
        write_json(self.manifest, records)

    def create(self, source: Path) -> Optional[Path]:
        """Copy an existing regular file into a unique timestamped backup."""

        source = source.expanduser().resolve()
        # Backups are intentionally limited to the three configuration files
        # owned by this application.
        source = allowed_restore_target(source, self.paths)
        if not source.exists():
            return None
        if not source.is_file():
            raise ToolError(f"cannot back up a non-regular file: {source}")
        ensure_private_dir(self.directory)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        name = f"{stamp}__{source.name}"
        destination = self.directory / name
        counter = 1
        while destination.exists():
            destination = self.directory / f"{stamp}__{counter}__{source.name}"
            counter += 1
        shutil.copy2(source, destination)
        record = {
            "backup": destination.name,
            "source": str(source),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_records(self._records() + [record])
        return destination

    def list(self) -> List[Dict[str, str]]:
        return sorted(self._records(), key=lambda item: item.get("created_at", ""), reverse=True)

    def resolve(self, backup_name: str) -> Path:
        if not backup_name or Path(backup_name).name != backup_name:
            raise SafetyError("backup name must be a filename, not a path")
        candidate = ensure_within(self.directory / backup_name, self.directory)
        if not candidate.is_file() or candidate.name == self.manifest.name:
            raise ToolError(f"backup not found: {backup_name}")
        return candidate

    def latest_for(self, filename: str) -> Optional[Dict[str, str]]:
        matches = [record for record in self.list() if Path(record.get("source", "")).name == filename]
        return matches[0] if matches else None

    def restore(self, backup_name: str, target: Path) -> Path:
        backup = self.resolve(backup_name)
        destination = allowed_restore_target(target, self.paths)
        ensure_private_dir(destination.parent)
        shutil.copy2(backup, destination)
        return destination
