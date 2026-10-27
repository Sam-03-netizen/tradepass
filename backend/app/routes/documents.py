import os, uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Document, Shipment, User
from ..schemas import DocumentResponse, ReviewFields
router = APIRouter(prefix="/shipments/{shipment_id}/documents", tags=["Documents"])
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}
ALLOWED_CATEGORIES = {"commercial_invoice", "packing_list", "certificate_of_origin", "lab_report", "product_certificate", "bill_of_lading", "customs_document", "other"}
def get_shipment(db, shipment_id, user):
    s = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.company_id == user.company_id).first()
    if not s: raise HTTPException(404, "Shipment not found")
    return s
@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(shipment_id: int, category: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    shipment = get_shipment(db, shipment_id, user)
    if category not in ALLOWED_CATEGORIES: raise HTTPException(422, "Unsupported document category")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXT: raise HTTPException(415, "Allowed formats: PDF, PNG, JPG, TXT, CSV")
    content_type = file.content_type or "application/octet-stream"
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if not data: raise HTTPException(400, "Empty file")
    if len(data) > max_bytes: raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
    # Basic MIME/extension check; this is not malware scanning.
    storage_dir = Path(settings.storage_dir).resolve() / str(user.company_id) / str(shipment.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    key = f"{uuid.uuid4().hex}{suffix}"
    path = storage_dir / key
    path.write_bytes(data)
    doc = Document(company_id=user.company_id, shipment_id=shipment.id, uploaded_by=user.id, original_filename=Path(file.filename or "document").name[:255], category=category, content_type=content_type, size_bytes=len(data), storage_key=str(path), processing_status="uploaded", review_status="pending", extracted_fields={}, reviewed_fields={})
    try: db.add(doc); db.commit(); db.refresh(doc); return doc
    except Exception:
        db.rollback(); path.unlink(missing_ok=True); raise
@router.get("/", response_model=list[DocumentResponse])
def list_documents(shipment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_shipment(db, shipment_id, user)
    return db.query(Document).filter(Document.shipment_id == shipment_id, Document.company_id == user.company_id).order_by(Document.created_at.desc()).all()
@router.get("/{document_id}/download")
def download_document(shipment_id: int, document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_shipment(db, shipment_id, user)
    doc = db.query(Document).filter(Document.id == document_id, Document.shipment_id == shipment_id, Document.company_id == user.company_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    path = Path(doc.storage_key)
    if not path.is_file(): raise HTTPException(404, "Stored file not found")
    return FileResponse(path, media_type=doc.content_type, filename=doc.original_filename, content_disposition_type="attachment")
@router.patch("/{document_id}/review", response_model=DocumentResponse)
def review_document(shipment_id: int, document_id: int, payload: ReviewFields, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_shipment(db, shipment_id, user)
    doc = db.query(Document).filter(Document.id == document_id, Document.shipment_id == shipment_id, Document.company_id == user.company_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    doc.reviewed_fields = payload.fields; doc.expiry_date = payload.expiry_date; doc.review_status = "reviewed"; doc.processing_status = "reviewed"
    db.commit(); db.refresh(doc); return doc
@router.delete("/{document_id}", status_code=204)
def delete_document(shipment_id: int, document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_shipment(db, shipment_id, user)
    doc = db.query(Document).filter(Document.id == document_id, Document.shipment_id == shipment_id, Document.company_id == user.company_id).first()
    if not doc: raise HTTPException(404, "Document not found")
    Path(doc.storage_key).unlink(missing_ok=True); db.delete(doc); db.commit(); return None
