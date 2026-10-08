from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.core.db import get_db
from app.schemas import NodeOut
from app.services import nodes as node_service
from app.services.blobstore import BlobStore, get_blob_store

router = APIRouter(tags=["files"])

READ_CHUNK = 1024 * 1024


def _read_limited(upload: UploadFile) -> bytes:
    limit = settings.max_upload_bytes
    buf = bytearray()
    while chunk := upload.file.read(READ_CHUNK):
        buf.extend(chunk)
        if len(buf) > limit:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"File exceeds the {limit} byte upload limit",
            )
    return bytes(buf)


@router.post("/files", response_model=NodeOut, status_code=201)
def upload_file(
    file: UploadFile = File(...),
    parent_id: str | None = Form(None),
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
    blobs: BlobStore = Depends(get_blob_store),
):
    data = _read_limited(file)
    return node_service.create_file(
        db,
        blobs,
        owner_id=user_id,
        name=file.filename or "untitled",
        parent_id=parent_id or None,
        data=data,
        content_type=file.content_type,
    )


@router.get("/files/{node_id}/content")
def download_file(
    node_id: str,
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
    blobs: BlobStore = Depends(get_blob_store),
):
    node = node_service.get_owned_node(db, user_id, node_id)
    if node.type != "file" or node.blob_key is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Node is not a file")
    data = blobs.get(node.blob_key)
    return Response(
        content=data,
        media_type=node.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(node.name)}"},
    )
