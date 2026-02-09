from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import db, BASE_DIR
from infrastructure.persistence.sqlalchemy.seed import seed_demo_pos

from api.routes.po_routes import router as po_router
from api.routes.material_routes import router as material_router
from api.routes.sap_routes import router as sap_router

app = FastAPI(title="POPR System")

app.include_router(po_router)
app.include_router(material_router)
app.include_router(sap_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def startup() -> None:
    await db.init_models()
    async with db.get_session() as session:
        data_path = BASE_DIR / "infrastructure" / "erp" / "demo_po_data.json"
        await seed_demo_pos(session, data_path)
