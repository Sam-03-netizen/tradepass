from datetime import date
from sqlalchemy.orm import Session
from ..models import Shipment, Document, ComplianceIssue

# Preliminary operational checklist only; actual requirements vary by product and destination.
DEFAULT_REQUIRED = {"commercial_invoice", "packing_list"}
def run_checks(db: Session, shipment: Shipment) -> list[ComplianceIssue]:
    docs = db.query(Document).filter(Document.shipment_id == shipment.id, Document.company_id == shipment.company_id).all()
    issues = []
    categories = {d.category for d in docs}
    for category in sorted(DEFAULT_REQUIRED - categories):
        issues.append(ComplianceIssue(company_id=shipment.company_id, shipment_id=shipment.id, code=f"missing_{category}", severity="warning", title=f"Missing {category.replace('_',' ')}", detail=f"No {category.replace('_',' ')} has been uploaded. This is a preliminary workflow checklist, not a legal determination."))
    for d in docs:
        fields = d.reviewed_fields or d.extracted_fields or {}
        if d.expiry_date:
            try:
                if date.fromisoformat(d.expiry_date) < date.today():
                    issues.append(ComplianceIssue(company_id=shipment.company_id, shipment_id=shipment.id, code=f"expired_document_{d.id}", severity="error", title=f"Expired document: {d.original_filename}", detail=f"Recorded expiry date {d.expiry_date} is in the past."))
            except ValueError: pass
        ref = fields.get("reference_number")
        if ref and str(ref).strip().casefold() != shipment.reference_number.casefold():
            issues.append(ComplianceIssue(company_id=shipment.company_id, shipment_id=shipment.id, code=f"reference_mismatch_{d.id}", severity="error", title="Shipment reference mismatch", detail=f"Document reference '{ref}' differs from shipment reference '{shipment.reference_number}'."))
        product = fields.get("product") or fields.get("product_description")
        if product and str(product).strip().casefold() != shipment.product.strip().casefold():
            issues.append(ComplianceIssue(company_id=shipment.company_id, shipment_id=shipment.id, code=f"product_mismatch_{d.id}", severity="warning", title="Product description mismatch", detail=f"Document product '{product}' differs from shipment product '{shipment.product}'."))
    return issues
