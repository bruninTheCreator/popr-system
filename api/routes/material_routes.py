from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...application.use_cases.process_material import (
    ProcessMaterialCommand,
    ProcessMaterialUseCase,
)
from ...application.ports.repository_port import RepositoryPort
from ...domain.entities.material_status import MaterialStatusEntry
from ..dependencies import (
    get_material_repository,
    get_process_material_use_case,
)

router = APIRouter(tags=["Materials"])


class MaterialStatusResponse(BaseModel):
    status: str
    timestamp: datetime


class ProcessMaterialRequest(BaseModel):
    material_id: str = Field(..., description="ID do material")
    minimum_stock: int = Field(..., description="Estoque minimo")
    notify_email: Optional[str] = Field(None, description="Email para notificacao")


class ProcessMaterialResponse(BaseModel):
    success: bool
    material_id: str
    message: str
    history: List[MaterialStatusResponse]


class MaterialHistoryResponse(BaseModel):
    material_id: str
    history: List[MaterialStatusResponse]


@router.post("/process-material", response_model=ProcessMaterialResponse)
def process_material(
    request: ProcessMaterialRequest,
    use_case: ProcessMaterialUseCase = Depends(get_process_material_use_case),
):
    command = ProcessMaterialCommand(
        material_id=request.material_id,
        minimum_stock=request.minimum_stock,
        notify_email=request.notify_email,
    )
    result = use_case.execute(command)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.message,
        )

    return ProcessMaterialResponse(
        success=result.success,
        material_id=result.material_id,
        message=result.message,
        history=_to_response_history(result.history),
    )


@router.get("/history/{material_id}", response_model=MaterialHistoryResponse)
def get_history(
    material_id: str,
    repository: RepositoryPort = Depends(get_material_repository),
):
    history = repository.get_history(material_id)
    return MaterialHistoryResponse(
        material_id=material_id,
        history=_to_response_history(history),
    )


def _to_response_history(history: List[MaterialStatusEntry]) -> List[MaterialStatusResponse]:
    return [
        MaterialStatusResponse(status=entry.status.value, timestamp=entry.timestamp)
        for entry in history
    ]
