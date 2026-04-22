"""API tests for procurement purchase-order workflows."""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common_master.models import Company, Project, Tax
from purchase_master.models import ProductCreation, UnitMaster

from .models import PurchaseOrder, PurchaseOrderApproval, Supplier


class PurchaseOrderApiTests(APITestCase):
    def setUp(self):
        # Shared master records are created once so each test can focus on the
        # procurement workflow instead of repeating setup assertions.
        self.company = Company.objects.create(name="Blue Planet", code="BPIVS")
        self.project = Project.objects.create(
            company=self.company,
            name="BAP2 / PIDUGURALLA",
            code="BAP2-001",
            project_date=date(2026, 4, 7),
        )
        self.supplier = Supplier.objects.create(
            name="AIR SHUDDHI ENGINEERS",
            gst_no="37ABCDE1234F1Z5",
            pan_no="ABCDE1234F",
            msme_type="Small",
            msme_no="MSME-001",
            contact_person="Procurement Lead",
            contact_no="9876543210",
        )
        self.product = ProductCreation.objects.create(
            company=self.company,
            product_name="Aeration Panel",
        )
        self.unit = UnitMaster.objects.create(
            unit_name="Nos",
            decimal_points=0,
        )
        self.tax = Tax.objects.create(name="GST 18", value=Decimal("18.00"))

    def purchase_order_payload(self):
        return {
            "company": self.company.pk,
            "project": self.project.pk,
            "supplier": self.supplier.pk,
            "po_type": "product",
            "pr_number": "PR-2026-001",
            "entry_date": "2026-04-07",
            "quotation_no": "QT-001",
            "quotation_date": "2026-04-07",
            "revision_no": "REV001",
            "payment_days": "30 days",
            "shipping_address": "Piduguralla Yard",
            "remarks": "Urgent dispatch",
            "items": [
                {
                    "product": self.product.pk,
                    "unit": self.unit.pk,
                    "qty": "2.00",
                    "rate": "100.00",
                    "discount_type": "percentage",
                    "discount_value": "10.00",
                    "tax": self.tax.pk,
                    "delivery_date": "2026-04-15",
                    "remarks": "Deliver to site",
                }
            ],
        }

    def test_create_purchase_order_uses_shared_master_tables(self):
        response = self.client.post(
            reverse("purchase-order-create"),
            data=self.purchase_order_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseOrder.objects.count(), 1)

        purchase_order = PurchaseOrder.objects.get()
        self.assertTrue(purchase_order.po_number.startswith("PO/2026-2027/BPIVS/"))
        self.assertEqual(purchase_order.company.pk, self.company.pk)
        self.assertEqual(purchase_order.project.pk, self.project.pk)
        self.assertEqual(purchase_order.total_basic_value, Decimal("180.00"))
        self.assertEqual(purchase_order.total_gst_amount, Decimal("32.40"))
        self.assertEqual(purchase_order.gross_amount, Decimal("212.40"))
        self.assertEqual(purchase_order.workflow_status, PurchaseOrder.WorkflowStatus.PENDING_L1)
        self.assertEqual(
            PurchaseOrderApproval.objects.filter(purchase_order=purchase_order).count(),
            3,
        )

    def test_purchase_order_list_matches_dashboard_shape(self):
        create_response = self.client.post(
            reverse("purchase-order-create"),
            data=self.purchase_order_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            reverse("purchase-order-list"),
            {"company": self.company.pk, "draw": 1, "start": 0, "length": 10},
        )
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["recordsFiltered"], 1)
        self.assertEqual(payload["data"][0]["company_name"], self.company.name)
        self.assertEqual(payload["data"][0]["project_name"], self.project.name)
        self.assertEqual(payload["data"][0]["supplier_name"], self.supplier.name)
        self.assertEqual(payload["data"][0]["approval_status"], "Pending (L1)")

    def test_level_approval_update_moves_po_to_next_dashboard(self):
        create_response = self.client.post(
            reverse("purchase-order-create"),
            data=self.purchase_order_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        purchase_order = PurchaseOrder.objects.get()
        approval_response = self.client.patch(
            reverse(
                "purchase-order-approval-update",
                kwargs={"pk": purchase_order.pk, "level": 1},
            ),
            data={"status": "approved"},
            format="json",
        )

        self.assertEqual(approval_response.status_code, status.HTTP_200_OK)
        purchase_order.refresh_from_db()
        self.assertEqual(
            purchase_order.workflow_status,
            PurchaseOrder.WorkflowStatus.APPROVED_L1,
        )

        level_2_response = self.client.get(
            reverse("purchase-order-approval-level-2-list"),
            {"draw": 1, "start": 0, "length": 10},
        )
        level_2_payload = level_2_response.json()

        self.assertEqual(level_2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(level_2_payload["recordsFiltered"], 1)
        self.assertEqual(level_2_payload["data"][0]["po_number"], purchase_order.po_number)
        self.assertEqual(level_2_payload["data"][0]["approval_status"], "pending")
        self.assertEqual(level_2_payload["data"][0]["appr_net_amount"], 180.0)
