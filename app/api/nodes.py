from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.db import get_db
from app.schemas import FolderCreate, NodeOut
from app.services import nodes as node_service

router = APIRouter(tags=["nodes"])


@router.post("/folders", response_model=NodeOut, status_code=201)
def create_folder(
    body: FolderCreate,
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    return node_service.create_folder(db, user_id, body.name, body.parent_id)


@router.get("/nodes", response_model=list[NodeOut])
def list_nodes(
    parent_id: str | None = None,
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    """List children of a folder. Omit parent_id to list the drive root."""
    return node_service.list_children(db, user_id, parent_id or None)


@router.get("/nodes/{node_id}", response_model=NodeOut)
def get_node(
    node_id: str,
    user_id: str = Depends(current_user),
    db: Session = Depends(get_db),
):
    return node_service.get_owned_node(db, user_id, node_id)
