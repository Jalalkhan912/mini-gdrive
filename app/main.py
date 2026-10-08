from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registers tables with Base)
from app.api import files, nodes
from app.core.db import Base, engine
from app.services.blobstore import get_blob_store


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema via create_all is fine for now; migrations (Alembic) come later.
    Base.metadata.create_all(bind=engine)
    get_blob_store().ensure_bucket()
    yield


app = FastAPI(title="Mini Google Drive", version="0.2.0", lifespan=lifespan)
app.include_router(nodes.router)
app.include_router(files.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
