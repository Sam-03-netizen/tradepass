from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Shipment, ComplianceIssue, User
from ..services.compliance import run_checks
from ..schemas import ResolveIssue
router = APIRouter(prefix="/shipments/{shipment_id}/compliance", tags=["Compliance"])
def get_owned(db, shipment_id, user):
    s=db.query(Shipment).filter(Shipment.id==shipment_id, Shipment.company_id==user.company_id).first()
    if not s: raise HTTPException(404,"Shipment not found")
    return s
@router.post("/run")
def run_compliance(shipment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s=get_owned(db, shipment_id, user)
    db.query(ComplianceIssue).filter(ComplianceIssue.shipment_id==s.id, ComplianceIssue.company_id==user.company_id, ComplianceIssue.resolved==False).delete(synchronize_session=False)
    issues=run_checks(db,s); db.add_all(issues); db.commit()
    return {"shipment_id":s.id,"note":"Preliminary workflow checks only; not a legal compliance determination.","issues":[{"id":i.id,"code":i.code,"severity":i.severity,"title":i.title,"detail":i.detail,"resolved":i.resolved} for i in issues]}
@router.get("/issues")
def list_issues(shipment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s=get_owned(db, shipment_id, user)
    rows=db.query(ComplianceIssue).filter(ComplianceIssue.shipment_id==s.id, ComplianceIssue.company_id==user.company_id).order_by(ComplianceIssue.created_at.desc()).all()
    return [{"id":i.id,"code":i.code,"severity":i.severity,"title":i.title,"detail":i.detail,"resolved":i.resolved} for i in rows]
@router.patch("/issues/{issue_id}")
def resolve_issue(shipment_id: int, issue_id: int, payload: ResolveIssue, db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    s=get_owned(db,shipment_id,user); issue=db.query(ComplianceIssue).filter(ComplianceIssue.id==issue_id, ComplianceIssue.shipment_id==s.id, ComplianceIssue.company_id==user.company_id).first()
    if not issue: raise HTTPException(404,"Issue not found")
    issue.resolved=payload.resolved; db.commit(); return {"id":issue.id,"resolved":issue.resolved}
