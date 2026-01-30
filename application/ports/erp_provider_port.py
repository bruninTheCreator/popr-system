from typing import List, Optional, Protocol


class ERPProviderPort(Protocol):
    def get_stock(self, material_id: str) -> Optional[int]:
        """Retorna o estoque atual do material ou None se nao cadastrado."""
        ...

    def get_open_pos(self, material_id: str) -> List[str]:
        """Retorna lista de POs abertas para o material."""
        ...
