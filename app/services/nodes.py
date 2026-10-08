import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Node
from app.services.blobstore import BlobStore

MAX_NAME_LENGTH = 255


def validate_name(name: str) -> str:
    name = name.strip()
    if not name or name in {".", ".."} or "/" in name or len(name) > MAX_NAME_LENGTH:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid name")
    return name


def get_owned_node(db: Session, owner_id: str, node_id: str) -> Node:
    # Other users' nodes return 404, not 403, so their existence is not revealed.
    node = db.get(Node, node_id)
    if node is None or node.deleted_at is not None or node.owner_id != owner_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Node not found")
    return node


def _ensure_parent_folder(db: Session, owner_id: str, parent_id: str | None) -> None:
    if parent_id is None:
        return
    parent = get_owned_node(db, owner_id, parent_id)
    if parent.type != "folder":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Parent must be a folder")


def _parent_clause(parent_id: str | None):
    return Node.parent_id.is_(None) if parent_id is None else Node.parent_id == parent_id


def _ensure_name_free(db: Session, owner_id: str, parent_id: str | None, name: str) -> None:
    # Check-then-insert: fine for a single node. A partial unique index is the
    # real fix under concurrency; that comes with the hardening work later.
    stmt = (
        select(Node.id)
        .where(
            Node.owner_id == owner_id,
            _parent_clause(parent_id),
            Node.name == name,
            Node.deleted_at.is_(None),
        )
        .limit(1)
    )
    if db.scalars(stmt).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A node with this name already exists here")


def create_folder(db: Session, owner_id: str, name: str, parent_id: str | None) -> Node:
    name = validate_name(name)
    _ensure_parent_folder(db, owner_id, parent_id)
    _ensure_name_free(db, owner_id, parent_id, name)
    node = Node(owner_id=owner_id, parent_id=parent_id, name=name, type="folder")
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def create_file(
    db: Session,
    blobs: BlobStore,
    owner_id: str,
    name: str,
    parent_id: str | None,
    data: bytes,
    content_type: str | None,
) -> Node:
    name = validate_name(name)
    _ensure_parent_folder(db, owner_id, parent_id)
    _ensure_name_free(db, owner_id, parent_id, name)

    # Write bytes first, then metadata. If the metadata write fails, remove the
    # blob so no orphaned bytes are left behind.
    node_id = str(uuid.uuid4())
    blob_key = f"{owner_id}/{node_id}"
    blobs.put(blob_key, data, content_type)
    node = Node(
        id=node_id,
        owner_id=owner_id,
        parent_id=parent_id,
        name=name,
        type="file",
        size_bytes=len(data),
        content_type=content_type,
        blob_key=blob_key,
    )
    try:
        db.add(node)
        db.commit()
    except Exception:
        db.rollback()
        blobs.delete(blob_key)
        raise
    db.refresh(node)
    return node


def list_children(db: Session, owner_id: str, parent_id: str | None) -> list[Node]:
    _ensure_parent_folder(db, owner_id, parent_id)
    stmt = (
        select(Node)
        .where(Node.owner_id == owner_id, _parent_clause(parent_id), Node.deleted_at.is_(None))
        .order_by(Node.type.desc(), Node.name)  # "folder" sorts before "file"
    )
    return list(db.scalars(stmt))
