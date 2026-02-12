from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PurchaseOrderModel(Base):
    __tablename__ = "purchase_orders"

    id = Column(String, primary_key=True, index=True)
    po_number = Column(String, unique=True, index=True, nullable=False)
    vendor_code = Column(String, nullable=False)
    vendor_name = Column(String, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="BRL", nullable=False)
    status = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    lock_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    sap_doc_number = Column(String, nullable=True)
    sap_fiscal_year = Column(String, nullable=True)
    sap_data = Column(JSON, nullable=False, default=dict)

    reconciliation_status = Column(String, nullable=True)
    reconciliation_notes = Column(Text, nullable=True)
    discrepancies = Column(JSON, nullable=False, default=list)

    created_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    events = Column(JSON, nullable=False, default=list)
    items = Column(JSON, nullable=False, default=list)
