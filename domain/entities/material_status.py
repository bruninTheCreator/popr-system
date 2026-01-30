from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MaterialStatus(str, Enum):
    RECEBIDO = "RECEBIDO"
    VERIFICANDO_CADASTRO = "VERIFICANDO_CADASTRO"
    CONSULTANDO_ESTOQUE = "CONSULTANDO_ESTOQUE"
    ESTOQUE_DISPONIVEL = "ESTOQUE_DISPONIVEL"
    SEM_ESTOQUE = "SEM_ESTOQUE"
    CONSULTANDO_PO = "CONSULTANDO_PO"
    PO_ENCONTRADA = "PO_ENCONTRADA"
    SEM_PO = "SEM_PO"


@dataclass(frozen=True)
class MaterialStatusEntry:
    material_id: str
    status: MaterialStatus
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "MaterialStatusEntry":
        return MaterialStatusEntry(
            material_id=data["material_id"],
            status=MaterialStatus(data["status"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
