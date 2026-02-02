from typing import List, Optional

from application.ports.erp_provider_port import ERPProviderPort


class SapGuiProvider(ERPProviderPort):
    """Stub para integracao SAP GUI."""

    def get_stock(self, material_id: str) -> Optional[int]:
        # TODO: Implementar integracao real com SAP GUI
        raise NotImplementedError("SAP provider ainda nao implementado.")

    def get_open_pos(self, material_id: str) -> List[str]:
        # TODO: Implementar integracao real com SAP GUI
        raise NotImplementedError("SAP provider ainda nao implementado.")
