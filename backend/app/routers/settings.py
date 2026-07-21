from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BlocklistTerm, AppSettingKV
from app.schemas import BlocklistTermIn, BlocklistTermOut

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/blocklist", response_model=list[BlocklistTermOut])
def list_blocklist(db: Session = Depends(get_db)):
    return db.query(BlocklistTerm).order_by(BlocklistTerm.category, BlocklistTerm.term).all()


@router.post("/blocklist", response_model=BlocklistTermOut)
def add_blocklist_term(payload: BlocklistTermIn, db: Session = Depends(get_db)):
    term = payload.term.strip()
    if not term:
        raise HTTPException(400, "Term cannot be empty")
    existing = db.query(BlocklistTerm).filter(BlocklistTerm.term.ilike(term)).first()
    if existing:
        return existing
    row = BlocklistTerm(term=term, category=payload.category)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/blocklist/{term_id}")
def delete_blocklist_term(term_id: int, db: Session = Depends(get_db)):
    row = db.get(BlocklistTerm, term_id)
    if not row:
        raise HTTPException(404, "Not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


def terms_by_category(db: Session) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in db.query(BlocklistTerm).all():
        out.setdefault(row.category, []).append(row.term)
    return out


@router.get("/app")
def get_app_settings(db: Session = Depends(get_db)):
    rows = db.query(AppSettingKV).all()
    return {r.key: r.value for r in rows}


@router.put("/app/{key}")
def set_app_setting(key: str, value: dict, db: Session = Depends(get_db)):
    row = db.get(AppSettingKV, key)
    if row is None:
        row = AppSettingKV(key=key, value=value.get("value"))
        db.add(row)
    else:
        row.value = value.get("value")
    db.commit()
    return {"key": key, "value": row.value}
