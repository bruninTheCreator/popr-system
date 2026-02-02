from typing import List, Protocol

from domain.entities.material_status import MaterialStatus, MaterialStatusEntry


class RepositoryPort(Protocol):
    def save_status(self, material_id: str, status: MaterialStatus) -> MaterialStatusEntry:
        """Persiste um novo status do material e retorna a entrada salva."""
        ...

    def get_history(self, material_id: str) -> List[MaterialStatusEntry]:
        """Retorna o historico completo do material."""
        ...
