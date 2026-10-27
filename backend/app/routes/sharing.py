import secrets, hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Shipment, Document, ShareLink, User
from ..schemas import ShareCreate
router=APIRouter(tags=["Buyer sharing"])
def owned(db, shipment_id, user):
 s=db.query(Shipment).filter(Shipment.id==shipment_id,Shipment.company_id==user.company_id).first()
 if not s: raise HTTPException(404,"Shipment not found")
 return s
@router.post("/shipments/{shipment_id}/share")
def create_share(shipment_id: int,payload: ShareCreate,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
 s=owned(db,shipment_id,user)
 docs=db.query(Document).filter(Document.shipment_id==s.id,Document.company_id==user.company_id).all()
 valid={d.id for d in docs}
 if any(i not in valid for i in payload.document_ids): raise HTTPException(400,"One or more documents do not belong to this shipment")
 token=secrets.token_urlsafe(32); digest=hashlib.sha256(token.encode()).hexdigest()
 row=ShareLink(company_id=user.company_id,shipment_id=s.id,token_hash=digest,document_ids=payload.document_ids,expires_at=datetime.now(timezone.utc)+timedelta(hours=payload.expires_in_hours))
 db.add(row); db.commit(); return {"share_id":row.id,"share_token":token,"expires_at":row.expires_at.isoformat(),"warning":"Copy this token now. This endpoint does not create a public URL; configure the frontend base URL to make a share link."}
@router.delete("/shares/{share_id}",status_code=204)
def revoke_share(share_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 row=db.query(ShareLink).filter(ShareLink.id==share_id,ShareLink.company_id==user.company_id).first()
 if not row: raise HTTPException(404,"Share link not found")
 row.revoked=True; db.commit(); return None
@router.get("/public/share/{token}")
def public_share(token:str,db:Session=Depends(get_db)):
 digest=hashlib.sha256(token.encode()).hexdigest(); row=db.query(ShareLink).filter(ShareLink.token_hash==digest).first()
 if not row or row.revoked: raise HTTPException(404,"Share link is invalid, expired, or revoked")
 expires = row.expires_at
 if expires.tzinfo is None: expires = expires.replace(tzinfo=timezone.utc)
 if expires <= datetime.now(timezone.utc): raise HTTPException(404,"Share link is invalid, expired, or revoked")
 s=db.query(Shipment).filter(Shipment.id==row.shipment_id,Shipment.company_id==row.company_id).first()
 if not s: raise HTTPException(404,"Shared shipment not found")
 docs=db.query(Document).filter(Document.id.in_(row.document_ids),Document.shipment_id==s.id,Document.company_id==s.company_id).all() if row.document_ids else []
 return {"shipment":{"reference_number":s.reference_number,"product":s.product,"origin_country":s.origin_country,"destination_country":s.destination_country,"status":s.status},"documents":[{"filename":d.original_filename,"category":d.category,"review_status":d.review_status} for d in docs],"note":"This is a limited read-only summary, not proof of authenticity or legal compliance."}
