from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.schemas.generic import build_read_model, build_write_model


def create_crud_router(
    model,
    prefix: str,
    tags: list[str],
    order_by=None,
    roles=(),
    exclude_write=(),
    name=None,
):
    """Factory router CRUD generik untuk entitas sederhana."""
    read_model = build_read_model(model, name=f"{model.__name__}Read" if name else None)
    write_model = build_write_model(model, exclude=exclude_write)

    router = APIRouter(prefix=prefix, tags=tags)

    auth = Depends(require_roles(*roles)) if roles else Depends(get_current_user)

    @router.get("", response_model=list[read_model])
    def list_items(
        skip: int = 0,
        limit: int = 200,
        db: Session = Depends(get_db),
        _=auth,
    ):
        query = db.query(model)
        if order_by is not None:
            query = query.order_by(order_by)
        return query.offset(skip).limit(limit).all()

    @router.get("/{item_id}", response_model=read_model)
    def get_item(item_id: int, db: Session = Depends(get_db), _=auth):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Data tidak ditemukan")
        return item

    @router.post("", response_model=read_model, status_code=status.HTTP_201_CREATED)
    def create_item(payload: write_model, db: Session = Depends(get_db), _=auth):
        data = payload.model_dump(exclude_unset=True)
        item = model(**{k: v for k, v in data.items() if v is not None})
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.put("/{item_id}", response_model=read_model)
    def update_item(item_id: int, payload: write_model, db: Session = Depends(get_db), _=auth):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Data tidak ditemukan")
        for k, v in payload.model_dump(exclude_unset=True).items():
            if v is not None:
                setattr(item, k, v)
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: int, db: Session = Depends(get_db), _=auth):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Data tidak ditemukan")
        db.delete(item)
        db.commit()

    return router
