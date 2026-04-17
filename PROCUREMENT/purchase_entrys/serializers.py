"""Serializers for procurement entry screens, dropdowns, and approvals."""

import uuid
from decimal import Decimal
from typing import Any, Mapping, cast

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from common_master.models import Tax as TaxMaster
from purchase_master.models import ItemMaster
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import UnitMaster

from .models import (
    GRN,
    PurchaseOrder,
    PurchaseOrderApproval,
    PurchaseRequisition,
    RateOrder,
    SRN,
    Supplier,
)


PO_DISCOUNT_PERCENTAGE = "percentage"
PO_DISCOUNT_AMOUNT = "amount"
PO_DISCOUNT_TYPE_CHOICES = (
    (PO_DISCOUNT_PERCENTAGE, "Percentage"),
    (PO_DISCOUNT_AMOUNT, "Amount"),
)


def _as_decimal(value, default="0.00"):
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def _decimal_to_json(value):
    return str(_as_decimal(value))


def _date_to_json(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _line_id(item_data, index):
    return item_data.get("id") or index


def _line_unique_id(item_data):
    return str(item_data.get("unique_id") or uuid.uuid4())


def _get_product(product_id):
    product = ProductMaster.objects.select_related("company").filter(pk=product_id).first()
    if product is None:
        raise serializers.ValidationError({"items": f"Product id {product_id} was not found."})
    return product


def _belongs_to_company(product, company):
    return getattr(product, "company_id", None) == getattr(company, "pk", None)


def _get_unit(unit_id):
    unit = UnitMaster.objects.filter(pk=unit_id).first()
    if unit is None:
        raise serializers.ValidationError({"items": f"Unit id {unit_id} was not found."})
    return unit


def _get_tax(tax_id):
    if not tax_id:
        return None
    tax = TaxMaster.objects.filter(pk=tax_id).first()
    if tax is None:
        raise serializers.ValidationError({"items": f"Tax id {tax_id} was not found."})
    return tax


def _get_item_master(item_id):
    item = ItemMaster.objects.select_related("unit").filter(pk=item_id).first()
    if item is None:
        raise serializers.ValidationError({"items": f"Item id {item_id} was not found."})
    return item


def _calculate_tax_amount(amount, tax):
    if not amount or not tax:
        return Decimal("0.00")
    return (amount * tax.value) / Decimal("100")


def _calculate_discounted_amount(qty, rate, discount_type, discount_value):
    base_amount = qty * rate
    if discount_type == PO_DISCOUNT_AMOUNT:
        discount_amount = discount_value
    else:
        discount_amount = (base_amount * discount_value) / Decimal("100")
    return max(base_amount - discount_amount, Decimal("0.00"))


def _calculate_receipt_amount(item_data):
    hundred = Decimal("100")
    qty = _as_decimal(item_data.get("received_qty"))
    rate = _as_decimal(item_data.get("rate"))
    tax = _as_decimal(item_data.get("tax_percent"))
    discount = _as_decimal(item_data.get("discount"))

    base = qty * rate
    tax_amount = base * (tax / hundred)
    return base + tax_amount - discount


class RateOrderLineSerializer(serializers.Serializer):
    """Single rate-order row stored in RateOrder.items_data."""

    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    item_name = serializers.CharField(max_length=255)
    rate = serializers.DecimalField(max_digits=10, decimal_places=3)
    from_date = serializers.DateField()
    to_date = serializers.DateField()

    def validate(self, attrs):
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        if attrs["from_date"] > attrs["to_date"]:
            raise serializers.ValidationError(
                {"to_date": "To date must be greater than or equal to from date."}
            )
        return attrs


class RateOrderSerializer(serializers.ModelSerializer):
    items = RateOrderLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = RateOrder
        fields = ["id", "unique_id", "supplier", "status", "created_at", "items"]
        read_only_fields = ["id", "unique_id", "created_at"]

    def validate(self, attrs):
        items = attrs.get("items_data")
        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "At least one rate row is required."})
        if items is not None and not items:
            raise serializers.ValidationError({"items": "At least one rate row is required."})
        return attrs

    def _normalise_items(self, items_data):
        rows = []
        for index, item in enumerate(items_data, start=1):
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "item_name": item["item_name"],
                    "rate": _decimal_to_json(item["rate"]),
                    "from_date": _date_to_json(item["from_date"]),
                    "to_date": _date_to_json(item["to_date"]),
                }
            )
        return rows

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        rate_order = RateOrder.objects.create(**validated_data)
        rate_order.items_data = self._normalise_items(items_data)
        rate_order.save(update_fields=["items_data"])
        return rate_order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if items_data is not None:
            instance.items_data = self._normalise_items(items_data)
        instance.save()
        return instance


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


class PurchaseOrderLineSerializer(serializers.Serializer):
    """Purchase-order line row stored in PurchaseOrder.items_data."""

    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    product = serializers.IntegerField()
    product_name = serializers.CharField(read_only=True)
    unit = serializers.IntegerField()
    unit_name = serializers.CharField(read_only=True)
    qty = serializers.DecimalField(max_digits=12, decimal_places=2)
    rate = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_type = serializers.ChoiceField(
        choices=PO_DISCOUNT_TYPE_CHOICES,
        default=PO_DISCOUNT_PERCENTAGE,
    )
    discount_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax = serializers.IntegerField(required=False, allow_null=True)
    tax_name = serializers.CharField(read_only=True)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    delivery_date = serializers.DateField(required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

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
    items = PurchaseOrderLineSerializer(many=True, source="items_data", required=False)

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
        items = attrs.get("items_data")
        company = attrs.get("company") or getattr(self.instance, "company", None)
        project = attrs.get("project") or getattr(self.instance, "project", None)
        supplier = attrs.get("supplier") or getattr(self.instance, "supplier", None)

        if company and project and project.company_id != company.id:
            raise serializers.ValidationError(
                {"project": "Selected project does not belong to the selected company."}
            )

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one product row is required."}
            )
        if items is not None and not items:
            raise serializers.ValidationError(
                {"items": "At least one product row is required."}
            )

        if items and company:
            for item in items:
                product = _get_product(item["product"])
                if not _belongs_to_company(product, company):
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"Product '{product.product_name}' does not belong to "
                                f"company '{company.name}'."
                            )
                        }
                    )
                _get_unit(item["unit"])
                _get_tax(item.get("tax"))

        if supplier:
            attrs.setdefault("supplier_gst_no", supplier.gst_no or "")
            attrs.setdefault("supplier_pan_no", supplier.pan_no or "")
            attrs.setdefault("supplier_msme_type", supplier.msme_type or "")
            attrs.setdefault("supplier_msme_no", supplier.msme_no or "")
            attrs.setdefault("supplier_contact_person", supplier.contact_person or "")
            attrs.setdefault("supplier_contact_no", supplier.contact_no or "")
        return attrs

    def _normalise_items(self, items_data, company):
        stored_items = []
        total_basic = Decimal("0.00")
        total_item_tax = Decimal("0.00")

        for index, item_data in enumerate(items_data, start=1):
            product = _get_product(item_data["product"])
            unit = _get_unit(item_data["unit"])
            tax = _get_tax(item_data.get("tax"))

            if company and not _belongs_to_company(product, company):
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Product '{product.product_name}' does not belong to "
                            f"company '{company.name}'."
                        )
                    }
                )

            qty = _as_decimal(item_data["qty"])
            rate = _as_decimal(item_data["rate"])
            discount_type = item_data.get("discount_type", PO_DISCOUNT_PERCENTAGE)
            discount_value = _as_decimal(item_data.get("discount_value"))
            tax_percent = tax.value if tax else Decimal("0.00")
            taxable_amount = _calculate_discounted_amount(
                qty,
                rate,
                discount_type,
                discount_value,
            )
            item_tax_amount = (taxable_amount * tax_percent) / Decimal("100")
            line_amount = taxable_amount + item_tax_amount

            stored_items.append(
                {
                    "id": _line_id(item_data, index),
                    "unique_id": _line_unique_id(item_data),
                    "product": product.pk,
                    "product_name": product.product_name,
                    "unit": unit.pk,
                    "unit_name": unit.unit_name,
                    "qty": _decimal_to_json(qty),
                    "rate": _decimal_to_json(rate),
                    "discount_type": discount_type,
                    "discount_value": _decimal_to_json(discount_value),
                    "tax": tax.pk if tax else None,
                    "tax_name": tax.name if tax else "",
                    "tax_percent": _decimal_to_json(tax_percent),
                    "amount": _decimal_to_json(line_amount),
                    "delivery_date": _date_to_json(item_data.get("delivery_date")),
                    "remarks": item_data.get("remarks") or "",
                }
            )

            total_basic += taxable_amount
            total_item_tax += item_tax_amount

        return stored_items, total_basic, total_item_tax

    def _stored_item_totals(self, stored_items):
        total_basic = Decimal("0.00")
        total_item_tax = Decimal("0.00")
        for item_data in stored_items:
            taxable_amount = _calculate_discounted_amount(
                _as_decimal(item_data.get("qty")),
                _as_decimal(item_data.get("rate")),
                item_data.get("discount_type", PO_DISCOUNT_PERCENTAGE),
                _as_decimal(item_data.get("discount_value")),
            )
            item_tax_amount = (
                taxable_amount * _as_decimal(item_data.get("tax_percent"))
            ) / Decimal("100")
            total_basic += taxable_amount
            total_item_tax += item_tax_amount
        return total_basic, total_item_tax

    def _save_amounts(self, purchase_order, stored_items, total_basic, total_item_tax):
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

        purchase_order.items_data = stored_items
        purchase_order.total_basic_value = total_basic
        purchase_order.freight_tax_amount = freight_tax_amount
        purchase_order.other_tax_amount = other_tax_amount
        purchase_order.packing_tax_amount = packing_tax_amount
        purchase_order.total_gst_amount = total_gst_amount
        purchase_order.gross_amount = gross_amount
        purchase_order.save(
            update_fields=[
                "items_data",
                "total_basic_value",
                "freight_tax_amount",
                "other_tax_amount",
                "packing_tax_amount",
                "total_gst_amount",
                "gross_amount",
                "updated_at",
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        stored_items, total_basic, total_item_tax = self._normalise_items(
            items_data,
            purchase_order.company,
        )
        self._save_amounts(purchase_order, stored_items, total_basic, total_item_tax)

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

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is None:
            stored_items = instance.items_data or []
            total_basic, total_item_tax = self._stored_item_totals(stored_items)
        else:
            stored_items, total_basic, total_item_tax = self._normalise_items(
                items_data,
                instance.company,
            )
        self._save_amounts(instance, stored_items, total_basic, total_item_tax)
        return instance


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
        validated_data = cast(Mapping[str, Any], self.validated_data)
        approval.status = validated_data["status"]
        approval.approved_net_amount = validated_data["approved_net_amount"]
        approval.approved_gross_amount = validated_data["approved_gross_amount"]
        approval.remarks = validated_data.get("remarks", "")
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


class PurchaseRequisitionLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    product_name = serializers.CharField(max_length=255)
    uom = serializers.CharField(max_length=50)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        return attrs


class PurchaseRequisitionListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    pr_number = serializers.CharField()
    company_name = serializers.CharField()
    project_name = serializers.CharField()
    requisition_for = serializers.CharField()
    requisition_type = serializers.CharField()
    requisition_date = serializers.DateField()
    requested_by = serializers.CharField()
    status = serializers.CharField()


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    items = PurchaseRequisitionLineSerializer(
        many=True,
        source="items_data",
        required=False,
    )

    class Meta:
        model = PurchaseRequisition
        fields = [
            "id",
            "pr_number",
            "company",
            "company_name",
            "project",
            "project_name",
            "requisition_for",
            "requisition_type",
            "requisition_date",
            "requested_by",
            "status",
            "created_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "company_name",
            "project_name",
            "created_at",
            "level1_status",
            "level1_approved_by",
            "level1_approved_at",
            "level1_remarks",
            "level2_status",
            "level2_approved_by",
            "level2_approved_at",
            "level2_remarks",
        ]

    def validate(self, attrs):
        items = attrs.get("items_data")
        company = attrs.get("company") or getattr(self.instance, "company", None)
        project = attrs.get("project") or getattr(self.instance, "project", None)

        if company and project and project.company_id != company.id:
            raise serializers.ValidationError(
                {"project": "Selected project does not belong to the selected company."}
            )

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one requisition row is required."}
            )
        if items is not None and not items:
            raise serializers.ValidationError(
                {"items": "At least one requisition row is required."}
            )

        return attrs

    def _normalise_items(self, items_data):
        rows = []
        for index, item in enumerate(items_data, start=1):
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "product_name": item["product_name"],
                    "uom": item["uom"],
                    "qty": _decimal_to_json(item["qty"]),
                    "remarks": item.get("remarks") or "",
                }
            )
        return rows

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        purchase_requisition = PurchaseRequisition.objects.create(**validated_data)
        purchase_requisition.items_data = self._normalise_items(items_data)
        purchase_requisition.save(update_fields=["items_data"])
        return purchase_requisition

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if items_data is not None:
            instance.items_data = self._normalise_items(items_data)
        instance.save()
        return instance


class GRNLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    product_name = serializers.CharField(max_length=255)
    uom = serializers.CharField(max_length=50)
    order_qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    previously_received_qty = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    received_qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        if attrs["order_qty"] < 0 or attrs["received_qty"] < 0:
            raise serializers.ValidationError(
                {"qty": "Order and received quantities cannot be negative."}
            )
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        return attrs


class GRNSerializer(serializers.ModelSerializer):
    items = GRNLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = GRN
        fields = [
            "id",
            "unique_id",
            "grn_number",
            "company",
            "project",
            "po",
            "supplier",
            "invoice_date",
            "supplier_invoice_no",
            "eway_bill_no",
            "eway_bill_date",
            "dc_no",
            "status",
            "level1_status",
            "level1_approved_by",
            "level1_approved_at",
            "level1_remarks",
            "level2_status",
            "level2_checked_by",
            "level2_checked_at",
            "level2_remarks",
            "description",
            "created_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "grn_number",
            "created_at",
            "level1_status",
            "level1_approved_by",
            "level1_approved_at",
            "level1_remarks",
            "level2_status",
            "level2_checked_by",
            "level2_checked_at",
            "level2_remarks",
        ]

    def validate(self, attrs):
        items = attrs.get("items_data")
        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "At least one GRN row is required."})
        if items is not None and not items:
            raise serializers.ValidationError({"items": "At least one GRN row is required."})
        return attrs

    def _normalise_items(self, items_data):
        rows = []
        for index, item in enumerate(items_data, start=1):
            amount = _calculate_receipt_amount(item)
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "product_name": item["product_name"],
                    "uom": item["uom"],
                    "order_qty": _decimal_to_json(item["order_qty"]),
                    "previously_received_qty": _decimal_to_json(
                        item.get("previously_received_qty", Decimal("0.00"))
                    ),
                    "received_qty": _decimal_to_json(item["received_qty"]),
                    "rate": _decimal_to_json(item["rate"]),
                    "tax_percent": _decimal_to_json(item["tax_percent"]),
                    "discount_type": item.get("discount_type") or "",
                    "discount": _decimal_to_json(item.get("discount", Decimal("0.00"))),
                    "amount": _decimal_to_json(amount),
                    "remarks": item.get("remarks") or "",
                }
            )
        return rows

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        grn = GRN.objects.create(**validated_data)
        grn.items_data = self._normalise_items(items_data)
        grn.save(update_fields=["items_data"])
        return grn

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if items_data is not None:
            instance.items_data = self._normalise_items(items_data)
        instance.save()
        return instance


class SRNLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    item = serializers.IntegerField()
    item_name = serializers.CharField(read_only=True)
    item_code = serializers.CharField(read_only=True)
    uom = serializers.CharField(read_only=True)
    order_qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    previously_received_qty = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    received_qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        if attrs["order_qty"] < 0 or attrs["received_qty"] < 0:
            raise serializers.ValidationError(
                {"qty": "Order and received quantities cannot be negative."}
            )
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        _get_item_master(attrs["item"])
        return attrs


class SRNSerializer(serializers.ModelSerializer):
    items = SRNLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = SRN
        fields = [
            "id",
            "unique_id",
            "srn_number",
            "company",
            "project",
            "po",
            "supplier",
            "po_date",
            "invoice_date",
            "tax_invoice_date",
            "supplier_invoice_no",
            "tax_invoice_no",
            "eway_bill_no",
            "eway_bill_date",
            "dc_no",
            "delivery_challan_no",
            "vehicle_no",
            "transporter",
            "received_at",
            "original_invoice",
            "oem_manual",
            "delivery_challan",
            "test_certificate",
            "amd_no",
            "cost_center",
            "basic",
            "paf",
            "freight_charges",
            "other_charges",
            "total_gst",
            "round_off",
            "total_amount",
            "status",
            "level1_status",
            "level1_approved_by",
            "level1_approved_at",
            "level1_remarks",
            "level2_status",
            "level2_approved_by",
            "level2_approved_at",
            "level2_remarks",
            "description",
            "created_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "srn_number",
            "created_at",
            "total_amount",
            "level1_status",
            "level1_approved_by",
            "level1_approved_at",
            "level1_remarks",
            "level2_status",
            "level2_approved_by",
            "level2_approved_at",
            "level2_remarks",
        ]

    def validate(self, attrs):
        items = attrs.get("items_data")
        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "At least one SRN row is required."})
        if items is not None and not items:
            raise serializers.ValidationError({"items": "At least one SRN row is required."})
        return attrs

    def _normalise_items(self, items_data):
        rows = []
        total_amount = Decimal("0.00")
        for index, item in enumerate(items_data, start=1):
            item_master = _get_item_master(item["item"])
            amount = _calculate_receipt_amount(item)
            unit = item_master.unit
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "item": item_master.pk,
                    "item_name": item_master.item_name,
                    "item_code": item_master.item_code,
                    "uom": unit.unit_name if unit else "",
                    "order_qty": _decimal_to_json(item["order_qty"]),
                    "previously_received_qty": _decimal_to_json(
                        item.get("previously_received_qty", Decimal("0.00"))
                    ),
                    "received_qty": _decimal_to_json(item["received_qty"]),
                    "rate": _decimal_to_json(item["rate"]),
                    "tax_percent": _decimal_to_json(item["tax_percent"]),
                    "discount_type": item.get("discount_type") or "",
                    "discount": _decimal_to_json(item.get("discount", Decimal("0.00"))),
                    "amount": _decimal_to_json(amount),
                    "remarks": item.get("remarks") or "",
                }
            )
            total_amount += amount
        return rows, total_amount

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        srn = SRN.objects.create(**validated_data)
        srn.items_data, srn.total_amount = self._normalise_items(items_data)
        srn.save(update_fields=["items_data", "total_amount"])
        return srn

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if items_data is not None:
            instance.items_data, instance.total_amount = self._normalise_items(items_data)
        else:
            instance.total_amount = sum(
                (_as_decimal(item.get("amount")) for item in instance.items_data or []),
                Decimal("0.00"),
            )
        instance.save()
        return instance
