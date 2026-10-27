from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Shipment, User
from ..schemas import ShipmentCreate, ShipmentUpdate, ShipmentResponse
router = APIRouter(prefix="/shipments", tags=["Shipments"])
def owned_shipment(db: Session, shipment_id: int, user: User) -> Shipment:
    item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.company_id == user.company_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    return item
@router.post("/", response_model=ShipmentResponse, status_code=201)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = Shipment(company_id=user.company_id, created_by=user.id, reference_number=payload.reference_number.strip(), product=payload.product.strip(), origin_country=payload.origin_country, destination_country=payload.destination_country, buyer_name=payload.buyer_name.strip() if payload.buyer_name else None, status="draft")
    db.add(item)
    try: db.commit(); db.refresh(item); return item
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="That shipment reference already exists for your company")
@router.get("/", response_model=list[ShipmentResponse])
def list_shipments(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Shipment).filter(Shipment.company_id == user.company_id)
    if status_filter: q = q.filter(Shipment.status == status_filter)
    return q.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)): return owned_shipment(db, shipment_id, user)
@router.patch("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(shipment_id: int, payload: ShipmentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_shipment(db, shipment_id, user)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None: setattr(item, key, value.strip() if isinstance(value, str) else value)
    db.commit(); db.refresh(item); return item
@router.delete("/{shipment_id}", status_code=204)
def archive_shipment(shipment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = owned_shipment(db, shipment_id, user); item.status = "on_hold"; db.commit(); return None
