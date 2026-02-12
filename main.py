from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.dependencies import db
from api.routes.po_routes import router as po_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_models()
    yield
    await db.engine.dispose()


app = FastAPI(title="POPR System", version="0.1.0", lifespan=lifespan)
app.include_router(po_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
