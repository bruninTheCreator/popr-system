from fastapi import FastAPI

from api.dependencies import db, BASE_DIR
from infrastructure.persistence.sqlalchemy.seed import seed_demo_pos

from api.routes.po_routes import router as po_router
from api.routes.material_routes import router as material_router

app = FastAPI(title="POPR System")

app.include_router(po_router)
app.include_router(material_router)


@app.on_event("startup")
async def startup() -> None:
    await db.init_models()
    async with db.get_session() as session:
        data_path = BASE_DIR / "infrastructure" / "erp" / "demo_po_data.json"
        await seed_demo_pos(session, data_path)
