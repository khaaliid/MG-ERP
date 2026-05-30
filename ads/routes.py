"""
API routes for the Ads service

Public:
  GET  /api/ads/active     → returns the highest-priority active ad (used by frontend AdSlot)

Manager-only (no auth enforced here; protect via reverse proxy or add token checks):
  GET    /api/ads           → list all ads
  POST   /api/ads           → create ad
  GET    /api/ads/{id}      → get one ad
  PUT    /api/ads/{id}      → update ad
  DELETE /api/ads/{id}      → delete ad
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Ad
from schemas import AdCreate, AdUpdate, AdResponse

router = APIRouter(prefix="/api/ads", tags=["ads"])


# ── Public endpoint ──────────────────────────────────────────────────────────

@router.get("/active", response_model=AdResponse, summary="Get the top active ad")
def get_active_ad(db: Session = Depends(get_db)):
    """
    Returns the single highest-priority active ad.
    This is the endpoint the frontend AdSlot backend-api slot calls.
    """
    ad = (
        db.query(Ad)
        .filter(Ad.is_active == True)
        .order_by(Ad.priority.desc(), Ad.created_at.desc())
        .first()
    )
    if not ad:
        raise HTTPException(status_code=404, detail="No active ads available")
    return ad


# ── Management endpoints ─────────────────────────────────────────────────────

@router.get("", response_model=List[AdResponse], summary="List all ads")
def list_ads(db: Session = Depends(get_db)):
    return db.query(Ad).order_by(Ad.priority.desc(), Ad.created_at.desc()).all()


@router.post("", response_model=AdResponse, status_code=status.HTTP_201_CREATED, summary="Create an ad")
def create_ad(payload: AdCreate, db: Session = Depends(get_db)):
    ad = Ad(**payload.model_dump())
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return ad


@router.get("/{ad_id}", response_model=AdResponse, summary="Get one ad")
def get_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad


@router.put("/{ad_id}", response_model=AdResponse, summary="Update an ad")
def update_ad(ad_id: int, payload: AdUpdate, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ad, field, value)
    db.commit()
    db.refresh(ad)
    return ad


@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an ad")
def delete_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    db.delete(ad)
    db.commit()
