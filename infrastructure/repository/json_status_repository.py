import json
from datetime import datetime
from pathlib import Path
from typing import List

from ...domain.entities.material_status import MaterialStatus, MaterialStatusEntry
from ...application.ports.repository_port import RepositoryPort


class JsonStatusRepository(RepositoryPort):
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write_data({"history": []})

    def save_status(self, material_id: str, status: MaterialStatus) -> MaterialStatusEntry:
        entry = MaterialStatusEntry(
            material_id=material_id,
            status=status,
            timestamp=datetime.now(),
        )
        data = self._read_data()
        data.setdefault("history", []).append(entry.to_dict())
        self._write_data(data)
        return entry

    def get_history(self, material_id: str) -> List[MaterialStatusEntry]:
        data = self._read_data()
        history = [
            MaterialStatusEntry.from_dict(item)
            for item in data.get("history", [])
            if item.get("material_id") == material_id
        ]
        return history

    def _read_data(self) -> dict:
        with self.storage_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_data(self, data: dict) -> None:
        with self.storage_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
