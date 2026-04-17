"""Shared approval models for the approvals app.

The purchase-order approval workflow is owned by ``purchase_entrys``.
This module re-exports those models so the approvals app can keep using
``from .models import PurchaseOrder`` without defining a second PO model.
"""

from purchase_entrys.models import PurchaseOrder, PurchaseOrderApproval

__all__ = ["PurchaseOrder", "PurchaseOrderApproval"]
