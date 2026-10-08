# Mini Google Drive

A learning project for system design: design, build, deploy, and monitor a file storage and sync service.

Design doc: see the Google Doc "Mini Google Drive - System Design" in the project owner's Drive.

## Stack
- Python 3.12, FastAPI
- PostgreSQL (metadata)
- MinIO, S3-compatible (file chunks)

## Run locally
```bash
docker compose up --build
curl http://localhost:8000/health
```

## Run tests
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Milestones
1. Single-node API skeleton, health check (current)
2. Folders and small file upload/download
3. Chunked resumable uploads with SHA-256 dedup
4. Sharing, permissions, trash
5. Versioning and restore
6. Change log and polling sync
7. Workers and garbage collection
8. CI/CD and AWS deployment
9. Metrics, tracing, SLO alerts
