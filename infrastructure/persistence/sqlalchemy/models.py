from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class POModel(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, index=True)
    po_number = Column(String(50), unique=True, index=True, nullable=False)
    vendor_code = Column(String(50), nullable=False)
    vendor_name = Column(String(255), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="BRL")
    status = Column(String(50), nullable=False, index=True)

    version = Column(Integer, nullable=False, default=1)

    locked_by = Column(String(100), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    lock_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    sap_doc_number = Column(String(50), nullable=True)
    sap_fiscal_year = Column(String(10), nullable=True)
    sap_data = Column(JSON, nullable=True)

    reconciliation_status = Column(String(50), nullable=True)
    reconciliation_notes = Column(String(500), nullable=True)
    discrepancies = Column(JSON, nullable=True)

    created_by = Column(String(100), nullable=False, default="system")
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(500), nullable=True)

    events = Column(JSON, nullable=True)

    items = relationship(
        "POItemModel",
        back_populates="po",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class POItemModel(Base):
    __tablename__ = "purchase_order_items"

    id = Column(String(36), primary_key=True, index=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)

    item_number = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    material_code = Column(String(50), nullable=True)

    po = relationship("POModel", back_populates="items")
