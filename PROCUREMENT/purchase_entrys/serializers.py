from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import (
    CompanyMaster,
    ProductMaster,
    ProjectMaster,
    PurchaseOrder,
    PurchaseOrderApproval,
    PurchaseOrderItem,
    Supplier,
    TaxMaster,
    UnitMaster,
)


def _calculate_tax_amount(amount, tax):
    if not amount or not tax:
        return Decimal("0.00")
    return (amount * tax.value) / Decimal("100")


class CompanyDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMaster
        fields = ["id", "name", "code"]


class ProjectDropdownSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = ProjectMaster
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "code",
            "gst_number",
            "pan_number",
            "contact_person",
            "contact_number",
        ]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "gst_no",
            "pan_no",
            "msme_type",
            "msme_no",
            "contact_person",
            "contact_no",
            "address",
            "is_active",
        ]


class ProductDropdownSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = ProductMaster
        fields = ["id", "company", "company_name", "product_name"]


class UnitDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitMaster
        fields = ["id", "unit_name", "decimal_points"]


class TaxDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxMaster
        fields = ["id", "name", "value"]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    unit_name = serializers.CharField(source="unit.unit_name", read_only=True)
    tax_name = serializers.CharField(source="tax.name", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit",
            "unit_name",
            "qty",
            "rate",
            "discount_type",
            "discount_value",
            "tax",
            "tax_name",
            "tax_percent",
            "amount",
            "delivery_date",
            "remarks",
        ]
        read_only_fields = [
            "id",
            "product_name",
            "unit_name",
            "tax_name",
            "tax_percent",
            "amount",
        ]

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        if attrs["discount_value"] < 0:
            raise serializers.ValidationError(
                {"discount_value": "Discount cannot be negative."}
            )
        return attrs


class PurchaseOrderSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    approval_status = serializers.CharField(source="approval_status_label", read_only=True)
    freight_tax_name = serializers.CharField(source="freight_tax.name", read_only=True)
    other_tax_name = serializers.CharField(source="other_tax.name", read_only=True)
    packing_tax_name = serializers.CharField(source="packing_tax.name", read_only=True)
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "company",
            "company_name",
            "project",
            "project_name",
            "supplier",
            "supplier_name",
            "po_type",
            "pr_number",
            "from_company",
            "entry_date",
            "supplier_gst_no",
            "supplier_pan_no",
            "supplier_msme_type",
            "supplier_msme_no",
            "supplier_contact_person",
            "supplier_contact_no",
            "quotation_no",
            "quotation_date",
            "revision_no",
            "revision_date",
            "revision_remarks",
            "total_basic_value",
            "freight_charges",
            "freight_tax",
            "freight_tax_name",
            "freight_tax_amount",
            "other_charges",
            "other_tax",
            "other_tax_name",
            "other_tax_amount",
            "packing_forwarding",
            "packing_tax",
            "packing_tax_name",
            "packing_tax_amount",
            "round_off",
            "total_gst_amount",
            "gross_amount",
            "payment_days",
            "other_terms_conditions",
            "shipping_address",
            "remarks",
            "workflow_status",
            "approval_status",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "po_number",
            "company_name",
            "project_name",
            "supplier_name",
            "freight_tax_amount",
            "other_tax_amount",
            "packing_tax_amount",
            "total_basic_value",
            "total_gst_amount",
            "gross_amount",
            "approval_status",
            "workflow_status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        items = attrs.get("items") or []
        company = attrs["company"]
        project = attrs["project"]
        supplier = attrs["supplier"]

        if project.company_id != company.id:
            raise serializers.ValidationError(
                {"project": "Selected project does not belong to the selected company."}
            )

        if not items:
            raise serializers.ValidationError(
                {"items": "At least one product row is required."}
            )

        for item in items:
            product = item["product"]
            if product.company_id != company.id:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Product '{product.product_name}' does not belong to "
                            f"company '{company.name}'."
                        )
                    }
                )

        attrs.setdefault("supplier_gst_no", supplier.gst_no or "")
        attrs.setdefault("supplier_pan_no", supplier.pan_no or "")
        attrs.setdefault("supplier_msme_type", supplier.msme_type or "")
        attrs.setdefault("supplier_msme_no", supplier.msme_no or "")
        attrs.setdefault("supplier_contact_person", supplier.contact_person or "")
        attrs.setdefault("supplier_contact_no", supplier.contact_no or "")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        total_basic = Decimal("0.00")
        total_item_tax = Decimal("0.00")

        for item_data in items_data:
            tax = item_data.get("tax")
            tax_percent = tax.value if tax else Decimal("0.00")

            base_amount = item_data["qty"] * item_data["rate"]
            if item_data["discount_type"] == PurchaseOrderItem.DiscountType.AMOUNT:
                discount_amount = item_data["discount_value"]
            else:
                discount_amount = (base_amount * item_data["discount_value"]) / Decimal("100")

            taxable_amount = max(base_amount - discount_amount, Decimal("0.00"))
            item_tax_amount = (taxable_amount * tax_percent) / Decimal("100")
            line_amount = taxable_amount + item_tax_amount

            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                tax_percent=tax_percent,
                amount=line_amount,
                **item_data,
            )

            total_basic += taxable_amount
            total_item_tax += item_tax_amount

        freight_tax_amount = _calculate_tax_amount(
            purchase_order.freight_charges,
            purchase_order.freight_tax,
        )
        other_tax_amount = _calculate_tax_amount(
            purchase_order.other_charges,
            purchase_order.other_tax,
        )
        packing_tax_amount = _calculate_tax_amount(
            purchase_order.packing_forwarding,
            purchase_order.packing_tax,
        )
        total_gst_amount = (
            total_item_tax + freight_tax_amount + other_tax_amount + packing_tax_amount
        )
        gross_amount = (
            total_basic
            + total_gst_amount
            + purchase_order.freight_charges
            + purchase_order.other_charges
            + purchase_order.packing_forwarding
            + purchase_order.round_off
        )

        purchase_order.total_basic_value = total_basic
        purchase_order.freight_tax_amount = freight_tax_amount
        purchase_order.other_tax_amount = other_tax_amount
        purchase_order.packing_tax_amount = packing_tax_amount
        purchase_order.total_gst_amount = total_gst_amount
        purchase_order.gross_amount = gross_amount
        purchase_order.save(
            update_fields=[
                "total_basic_value",
                "freight_tax_amount",
                "other_tax_amount",
                "packing_tax_amount",
                "total_gst_amount",
                "gross_amount",
                "updated_at",
            ]
        )

        PurchaseOrderApproval.objects.bulk_create(
            [
                PurchaseOrderApproval(
                    purchase_order=purchase_order,
                    level=PurchaseOrderApproval.Level.LEVEL_1,
                ),
                PurchaseOrderApproval(
                    purchase_order=purchase_order,
                    level=PurchaseOrderApproval.Level.LEVEL_2,
                ),
                PurchaseOrderApproval(
                    purchase_order=purchase_order,
                    level=PurchaseOrderApproval.Level.LEVEL_3,
                ),
            ]
        )

        return purchase_order


class PurchaseOrderApprovalActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=PurchaseOrderApproval.Status.choices)
    approved_net_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )
    approved_gross_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        approval = self.context["approval"]
        status_value = attrs["status"]

        if approval.level > PurchaseOrderApproval.Level.LEVEL_1:
            previous_level = approval.level - 1
            previous_approval = approval.purchase_order.approvals.filter(
                level=previous_level
            ).first()
            if not previous_approval or previous_approval.status != PurchaseOrderApproval.Status.APPROVED:
                raise serializers.ValidationError(
                    f"Level {previous_level} approval must be approved first."
                )

        if status_value == PurchaseOrderApproval.Status.APPROVED:
            attrs.setdefault(
                "approved_net_amount",
                approval.purchase_order.total_basic_value,
            )
            attrs.setdefault(
                "approved_gross_amount",
                approval.purchase_order.gross_amount,
            )
        else:
            attrs.setdefault("approved_net_amount", Decimal("0.00"))
            attrs.setdefault("approved_gross_amount", Decimal("0.00"))

        return attrs

    def save(self, **kwargs):
        approval = self.context["approval"]
        approval.status = self.validated_data["status"]
        approval.approved_net_amount = self.validated_data["approved_net_amount"]
        approval.approved_gross_amount = self.validated_data["approved_gross_amount"]
        approval.remarks = self.validated_data.get("remarks", "")
        approval.approved_at = (
            timezone.now()
            if approval.status == PurchaseOrderApproval.Status.APPROVED
            else None
        )
        approval.save(
            update_fields=[
                "status",
                "approved_net_amount",
                "approved_gross_amount",
                "remarks",
                "approved_at",
                "updated_at",
            ]
        )
        approval.purchase_order.sync_workflow_status()
        return approval
