import json
from pathlib import Path
from typing import List, Optional

from application.ports.erp_provider_port import ERPProviderPort


class DemoProvider(ERPProviderPort):
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        if not self.data_path.exists():
            raise FileNotFoundError(f"Demo data not found: {self.data_path}")

    def get_stock(self, material_id: str) -> Optional[int]:
        data = self._read_data()
        material = data.get("materials", {}).get(material_id)
        if material is None:
            return None
        return int(material.get("stock", 0))

    def get_open_pos(self, material_id: str) -> List[str]:
        data = self._read_data()
        material = data.get("materials", {}).get(material_id, {})
        return list(material.get("open_pos", []))

    def _read_data(self) -> dict:
        with self.data_path.open("r", encoding="utf-8") as file:
            return json.load(file)
