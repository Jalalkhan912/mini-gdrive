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

## API (milestone 2)
Every request needs an `X-User-Id` header. This is a temporary stub, not authentication:
anyone can send any user ID. JWT auth arrives in milestone 4.

```bash
# Create a folder at the root
curl -X POST localhost:8000/folders -H "X-User-Id: alice" \
  -H "Content-Type: application/json" -d '{"name": "Projects"}'

# Upload a file into it (parent_id from the response above)
curl -X POST localhost:8000/files -H "X-User-Id: alice" \
  -F "file=@notes.txt" -F "parent_id=<folder-id>"

# List children (omit parent_id for the root), then download
curl localhost:8000/nodes -H "X-User-Id: alice"
curl localhost:8000/files/<file-id>/content -H "X-User-Id: alice" -o notes.txt
```

Uploads are capped at 100 MB per file for now. Chunked uploads come in milestone 3.

## Milestones
1. Single-node API skeleton, health check (done)
2. Folders and small file upload/download (done)
3. Chunked resumable uploads with SHA-256 dedup
4. Sharing, permissions, trash
5. Versioning and restore
6. Change log and polling sync
7. Workers and garbage collection
8. CI/CD and AWS deployment
9. Metrics, tracing, SLO alerts
