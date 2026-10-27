from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, get_db
from . import models  # registers all SQLAlchemy models
from .config import settings
from .dependencies import get_current_user
from .models import User
from .routes import auth, shipments, documents, compliance, sharing

# For this MVP, create_all creates missing tables. Existing schemas require migrations.
Base.metadata.create_all(bind=engine)
app = FastAPI(title="TradePass API", description="Shipment documentation and preliminary compliance workflow", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router); app.include_router(shipments.router); app.include_router(documents.router); app.include_router(compliance.router); app.include_router(sharing.router)
@app.get("/")
def root(): return {"message":"TradePass API is running", "docs":"/docs"}
@app.get("/health")
def health(): return {"status":"healthy"}
@app.get("/me")
def me(user: User = Depends(get_current_user)):
 return {"id":user.id,"name":user.name,"email":user.email,"company_id":user.company_id,"role":user.role}
@app.get("/dashboard/summary")
def dashboard(db = Depends(get_db), user: User = Depends(get_current_user)):
 from .models import Shipment, Document, ComplianceIssue
 q=db.query(Shipment).filter(Shipment.company_id==user.company_id)
 shipments=q.all(); ids=[s.id for s in shipments]
 docs=db.query(Document).filter(Document.company_id==user.company_id).all()
 issues=db.query(ComplianceIssue).filter(ComplianceIssue.company_id==user.company_id,ComplianceIssue.resolved==False).all()
 return {"total_shipments":len(shipments),"by_status":{status:sum(1 for s in shipments if s.status==status) for status in ["draft","in_progress","ready_for_review","completed","on_hold"]},"documents_count":len(docs),"pending_documents":sum(1 for d in docs if d.review_status=="pending"),"open_issues":len(issues),"recent_shipments":[{"id":s.id,"reference_number":s.reference_number,"product":s.product,"destination_country":s.destination_country,"status":s.status,"created_at":s.created_at.isoformat()} for s in sorted(shipments,key=lambda x:x.created_at,reverse=True)[:5]]}
