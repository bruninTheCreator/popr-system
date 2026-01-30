from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..ports.erp_provider_port import ERPProviderPort
from ..ports.notification_port import NotificationPort
from ..ports.repository_port import RepositoryPort
from ...domain.entities.material_status import MaterialStatus, MaterialStatusEntry


@dataclass
class ProcessMaterialCommand:
    material_id: str
    minimum_stock: int
    notify_email: Optional[str] = None


@dataclass
class ProcessMaterialResult:
    success: bool
    material_id: str
    message: str
    history: List[MaterialStatusEntry]


class ProcessMaterialUseCase:
    def __init__(
        self,
        erp_provider: ERPProviderPort,
        repository: RepositoryPort,
        notifier: NotificationPort,
    ) -> None:
        self.erp_provider = erp_provider
        self.repository = repository
        self.notifier = notifier

    def execute(self, command: ProcessMaterialCommand) -> ProcessMaterialResult:
        history: List[MaterialStatusEntry] = []

        history.append(self._save(command.material_id, MaterialStatus.RECEBIDO))
        history.append(self._save(command.material_id, MaterialStatus.VERIFICANDO_CADASTRO))

        stock = self.erp_provider.get_stock(command.material_id)
        if stock is None:
            return ProcessMaterialResult(
                success=False,
                material_id=command.material_id,
                message="Material nao cadastrado.",
                history=history,
            )

        history.append(self._save(command.material_id, MaterialStatus.CONSULTANDO_ESTOQUE))

        if stock >= command.minimum_stock:
            history.append(self._save(command.material_id, MaterialStatus.ESTOQUE_DISPONIVEL))
            return ProcessMaterialResult(
                success=True,
                material_id=command.material_id,
                message="Estoque suficiente.",
                history=history,
            )

        history.append(self._save(command.material_id, MaterialStatus.SEM_ESTOQUE))
        history.append(self._save(command.material_id, MaterialStatus.CONSULTANDO_PO))

        open_pos = self.erp_provider.get_open_pos(command.material_id)
        if open_pos:
            history.append(self._save(command.material_id, MaterialStatus.PO_ENCONTRADA))
            return ProcessMaterialResult(
                success=True,
                material_id=command.material_id,
                message="PO aberta encontrada.",
                history=history,
            )

        history.append(self._save(command.material_id, MaterialStatus.SEM_PO))

        if command.notify_email:
            subject = f"[POPR] Material {command.material_id} sem PO"
            body = (
                "Material sem estoque minimo e sem PO aberta. "
                f"Processado em {datetime.now().isoformat()}"
            )
            self.notifier.send_email(command.notify_email, subject, body)

        return ProcessMaterialResult(
            success=True,
            material_id=command.material_id,
            message="Material sem PO aberta.",
            history=history,
        )

    def _save(self, material_id: str, status: MaterialStatus) -> MaterialStatusEntry:
        return self.repository.save_status(material_id, status)
