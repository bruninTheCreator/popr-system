from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import os
from pathlib import Path

from infrastructure.sap.demo_sap_gateway import DemoSAPGateway

router = APIRouter(prefix="/api/v1/sap", tags=["SAP"])


class ConnectVMRequest(BaseModel):
    host: str
    port: str | None = None
    username: str | None = None
    password: str | None = None


class ConnectVMResponse(BaseModel):
    connected: bool
    message: str


@router.post("/connect-vm", response_model=ConnectVMResponse)
async def connect_vm(payload: ConnectVMRequest):
    """
    Endpoint para iniciar uma 'conexão' ao SAP via VM.

    Para o modo demo, utiliza o DemoSAPGateway e chama `connect()`.
    Para modo 'sap' (real), responde 501 (não implementado aqui).
    """
    provider = os.getenv("POPR_SAP_PROVIDER", "demo").lower()
    if provider == "demo":
        base_dir = Path(__file__).resolve().parents[2]
        demo_path = base_dir / "infrastructure" / "erp" / "demo_po_data.json"
        gateway = DemoSAPGateway(demo_path)
        try:
            ok = await gateway.connect()
            if ok:
                return ConnectVMResponse(connected=True, message=f"Conectado ao SAP (demo) em {payload.host}")
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao conectar (demo)")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Para provider real, deixamos claro que não implementamos a abertura de sessão via VM neste endpoint
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Conexão a SAP via VM não implementada no servidor. Use adapter local ou configure POPR_SAP_PROVIDER=demo para testes.")
