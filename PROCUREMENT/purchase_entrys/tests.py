"""Phase-7 test coverage for procurement module-reference refactor."""

import importlib
from datetime import date
from decimal import Decimal

from django.db import models as dj_models
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common_master.models import Company, Project, Tax
from purchase_master.models import ProductCreation, UnitMaster

from .models import (
    GRN,
    PurchaseOrder,
    PurchaseOrderApproval,
    PurchaseRequisition,
    RateOrder,
    SRN,
    SRNItem,
    Supplier,
)
from .serializers import (
    GRNSerializer,
    PurchaseOrderSerializer,
    PurchaseRequisitionSerializer,
    SRNSerializer,
)
from .services import generated_supplier_code


class PurchaseEntryUnitTests(SimpleTestCase):
    def test_generated_supplier_code_uses_zero_padded_sequence(self):
        self.assertEqual(generated_supplier_code(7), "SUP-00007")
        self.assertEqual(generated_supplier_code(123), "SUP-00123")
        self.assertIsNone(generated_supplier_code(None))


class PurchaseEntryArchitectureTests(SimpleTestCase):
    def test_models_do_not_keep_cross_database_foreign_keys(self):
        forbidden_apps = {"common_master", "purchase_master"}
        models_to_check = [
            RateOrder,
            Supplier,
            PurchaseOrder,
            PurchaseOrderApproval,
            PurchaseRequisition,
            GRN,
            SRN,
            SRNItem,
        ]

        for model in models_to_check:
            for field in model._meta.get_fields():
                if not isinstance(field, dj_models.ForeignKey):
                    continue
                remote_model = field.remote_field.model
                remote_app = getattr(getattr(remote_model, "_meta", None), "app_label", "")
                self.assertNotIn(
                    remote_app,
                    forbidden_apps,
                    msg=(
                        f"{model.__name__}.{field.name} still points at "
                        f"{remote_app}.{remote_model.__name__}"
                    ),
                )

    def test_transaction_serializers_expose_business_code_fields(self):
        self.assertIn("company_code", PurchaseOrderSerializer().fields)
        self.assertIn("supplier_code", PurchaseOrderSerializer().fields)
        self.assertNotIn("company", PurchaseOrderSerializer().fields)
        self.assertNotIn("supplier", PurchaseOrderSerializer().fields)

        self.assertIn("company_code", PurchaseRequisitionSerializer().fields)
        self.assertNotIn("company", PurchaseRequisitionSerializer().fields)

        self.assertIn("company_code", GRNSerializer().fields)
        self.assertIn("supplier_code", GRNSerializer().fields)
        self.assertIn("company_code", SRNSerializer().fields)
        self.assertIn("supplier_code", SRNSerializer().fields)

    def test_module_reference_migration_order_is_add_then_populate_then_remove(self):
        migration = importlib.import_module(
            "purchase_entrys.migrations.0005_purchase_entrys_module_references"
        )
        operations = migration.Migration.operations

        operation_types = [operation.__class__.__name__ for operation in operations]
        self.assertIn("RunPython", operation_types)
        self.assertEqual(operation_types[0], "AddField")
        self.assertEqual(operation_types[-1], "RemoveField")

        add_fields = {
            (operation.model_name, operation.name)
            for operation in operations
            if operation.__class__.__name__ == "AddField"
        }
        remove_fields = {
            (operation.model_name, operation.name)
            for operation in operations
            if operation.__class__.__name__ == "RemoveField"
        }

        self.assertIn(("supplier", "supplier_code"), add_fields)
        self.assertIn(("purchaseorder", "company_code"), add_fields)
        self.assertIn(("purchaseorder", "supplier_code"), add_fields)
        self.assertIn(("purchaserequisition", "company_code"), add_fields)
        self.assertIn(("grn", "supplier_code"), add_fields)
        self.assertIn(("srnitem", "item_code"), add_fields)

        self.assertIn(("purchaseorder", "company"), remove_fields)
        self.assertIn(("purchaseorder", "supplier"), remove_fields)
        self.assertIn(("srnitem", "item"), remove_fields)

        run_python_index = next(
            index
            for index, operation in enumerate(operations)
            if operation.__class__.__name__ == "RunPython"
        )
        first_remove_index = next(
            index
            for index, operation in enumerate(operations)
            if operation.__class__.__name__ == "RemoveField"
        )
        self.assertLess(run_python_index, first_remove_index)


class PurchaseOrderApiTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Blue Planet", code="BPIVS")
        self.project = Project.objects.create(
            company=self.company,
            name="BAP2 / PIDUGURALLA",
            code="BAP2-001",
            project_date=date(2026, 4, 7),
        )
        self.supplier = Supplier.objects.create(
            supplier_code="SUP-00001",
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
            "company_code": self.company.code,
            "project_code": self.project.code,
            "supplier_code": self.supplier.supplier_code,
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

    def purchase_requisition_payload(self):
        return {
            "company_code": self.company.code,
            "project_code": self.project.code,
            "requisition_for": "Direct",
            "requisition_type": "Regular",
            "requisition_date": "2026-04-07",
            "requested_by": "Procurement Lead",
            "items": [
                {
                    "product_name": "Aeration Panel",
                    "uom": "Nos",
                    "qty": "2.00",
                    "remarks": "Need soon",
                    "delivery_date": "2026-04-15",
                }
            ],
        }

    def test_create_purchase_order_uses_business_codes(self):
        response = self.client.post(
            reverse("purchase-order-create"),
            data=self.purchase_order_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PurchaseOrder.objects.count(), 1)

        purchase_order = PurchaseOrder.objects.get()
        self.assertTrue(purchase_order.po_number.startswith("PO/2026-2027/BPIVS/"))
        self.assertEqual(purchase_order.company_code, self.company.code)
        self.assertEqual(purchase_order.project_code, self.project.code)
        self.assertEqual(purchase_order.supplier_code, self.supplier.supplier_code)
        self.assertEqual(purchase_order.supplier_name, self.supplier.name)
        self.assertEqual(purchase_order.total_basic_value, Decimal("180.00"))
        self.assertEqual(purchase_order.total_gst_amount, Decimal("32.40"))
        self.assertEqual(purchase_order.gross_amount, Decimal("212.40"))
        self.assertEqual(
            PurchaseOrderApproval.objects.filter(purchase_order=purchase_order).count(),
            3,
        )

    def test_purchase_order_list_matches_code_based_dashboard_shape(self):
        create_response = self.client.post(
            reverse("purchase-order-create"),
            data=self.purchase_order_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            reverse("purchase-order-list"),
            {"company": self.company.code, "draw": 1, "start": 0, "length": 10},
        )
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["recordsFiltered"], 1)
        self.assertEqual(payload["data"][0]["company_name"], self.company.code)
        self.assertEqual(payload["data"][0]["project_name"], self.project.code)
        self.assertEqual(payload["data"][0]["supplier_name"], self.supplier.name)
        self.assertEqual(payload["data"][0]["approval_status"], "Pending (L1)")

    def test_purchase_order_detail_exposes_code_fields(self):
        create_response = self.client.post(
            reverse("purchase-order-create"),
            data=self.purchase_order_payload(),
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        purchase_order = PurchaseOrder.objects.get()
        response = self.client.get(
            reverse("purchase-order-detail", kwargs={"pk": purchase_order.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["company_code"], self.company.code)
        self.assertEqual(payload["company_name"], self.company.code)
        self.assertEqual(payload["project_code"], self.project.code)
        self.assertEqual(payload["supplier_code"], self.supplier.supplier_code)
        self.assertEqual(payload["supplier_name"], self.supplier.name)
        self.assertEqual(payload["approval_status"], "Pending (L1)")

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
        self.assertEqual(level_2_payload["data"][0]["company_name"], self.company.code)
        self.assertEqual(level_2_payload["data"][0]["supplier_name"], self.supplier.name)
        self.assertEqual(level_2_payload["data"][0]["approval_status"], "pending")

    def test_purchase_requisition_create_and_sublist_use_codes(self):
        response = self.client.post(
            reverse("purchase-requisition-create"),
            data=self.purchase_requisition_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        requisition = PurchaseRequisition.objects.get()
        self.assertEqual(requisition.company_code, self.company.code)
        self.assertEqual(requisition.project_code, self.project.code)
        self.assertTrue(requisition.pr_number.startswith("PR/2026-2027/BPIVS/"))

        sublist_response = self.client.get(
            reverse("purchase-requisition-sublist"),
            {"company": self.company.code, "project": self.project.code},
        )
        sublist_payload = sublist_response.json()

        self.assertEqual(sublist_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(sublist_payload["data"]), 1)
        self.assertEqual(sublist_payload["data"][0]["pr_number"], requisition.pr_number)
        self.assertEqual(sublist_payload["data"][0]["product_name"], "Aeration Panel")

        approval_list_response = self.client.get(
            reverse("purchase-requisition-approval-list"),
            {"company": self.company.code, "project": self.project.code},
        )
        approval_payload = approval_list_response.json()

        self.assertEqual(approval_list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approval_payload["data"][0]["company_name"], self.company.code)
        self.assertEqual(approval_payload["data"][0]["project_name"], self.project.code)





