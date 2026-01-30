from fastapi import FastAPI

from .routes.po_routes import router as po_router
from .routes.material_routes import router as material_router

app = FastAPI(title="POPR System")

app.include_router(po_router)
app.include_router(material_router)
