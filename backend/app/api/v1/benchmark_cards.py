from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import BenchmarkCard

router=APIRouter()
@router.get('')
def cards(db:Session=Depends(get_db)):
 return {"items":[{"id":str(c.id),"run_id":str(c.run_id),"integrity_status":c.integrity_status,"manifest_hash":c.manifest_hash,"created_at":c.created_at.isoformat()} for c in db.scalars(select(BenchmarkCard).order_by(BenchmarkCard.created_at.desc()))]}
