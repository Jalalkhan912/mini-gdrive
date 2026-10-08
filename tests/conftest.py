import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.db import Base, get_db
from app.main import app
from app.services.blobstore import get_blob_store


class FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, key, data, content_type=None):
        self.objects[key] = data

    def get(self, key):
        return self.objects[key]

    def delete(self, key):
        self.objects.pop(key, None)


@pytest.fixture
def client():
    # Fresh in-memory SQLite and fake blob store per test. TestClient is used
    # without a context manager so the real lifespan (Postgres/MinIO) doesn't run.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    blobs = FakeBlobStore()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_blob_store] = lambda: blobs
    test_client = TestClient(app)
    test_client.blobs = blobs
    yield test_client
    app.dependency_overrides.clear()
