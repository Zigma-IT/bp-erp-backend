"""Serializers for purchase expense screens and dropdowns."""

import uuid
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import UnitMaster

from .models import PurchaseExpense


def _masters_db_alias():
    return "masters_db1"


def _as_decimal(value):
    if value in (None, ""):
        return Decimal("0.00")
    return Decimal(str(value))


def _decimal_to_str(value):
    return str(_as_decimal(value))


def _line_id(item, fallback):
    return item.get("id") or fallback


def _line_unique_id(item):
    value = item.get("unique_id")
    return str(value) if value else str(uuid.uuid4())


def _get_product(product_id):
    try:
        return ProductMaster.objects.using(_masters_db_alias()).get(pk=product_id)
    except ProductMaster.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"items": f"Invalid product id '{product_id}'."}
        ) from exc


def _get_unit(unit_id):
    try:
        return UnitMaster.objects.using(_masters_db_alias()).get(pk=unit_id)
    except UnitMaster.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"items": f"Invalid unit id '{unit_id}'."}
        ) from exc


def _sync_local_company(master_company):
    local_company, _ = CompanyMaster.objects.update_or_create(
        pk=master_company.pk,
        defaults={
            "name": master_company.name,
            "code": master_company.code,
            "country": None,
            "state": None,
            "city": None,
            "pincode": master_company.pincode,
            "latitude": master_company.latitude,
            "longitude": master_company.longitude,
            "is_active": master_company.is_active,
        },
    )
    return local_company


def _sync_local_project(master_project):
    local_company = _sync_local_company(master_project.company)
    local_project, _ = ProjectMaster.objects.update_or_create(
        pk=master_project.pk,
        defaults={
            "company": local_company,
            "name": master_project.name,
            "code": master_project.code,
            "client_name": master_project.client_name,
            "application_type": None,
            "capacity": master_project.capacity,
            "duration": master_project.duration,
            "project_date": master_project.project_date,
            "country": None,
            "state": None,
            "city": None,
            "address": master_project.address,
            "latitude": master_project.latitude,
            "longitude": master_project.longitude,
            "pincode": master_project.pincode,
            "pan_number": master_project.pan_number,
            "gst_number": master_project.gst_number,
            "gst_reg_date": master_project.gst_reg_date,
            "contact_person": master_project.contact_person,
            "contact_number": master_project.contact_number,
            "contact_email": master_project.contact_email,
            "website": master_project.website,
            "description": master_project.description,
            "is_active": master_project.is_active,
        },
    )
    return local_project


def _calculate_item_amounts(qty, rate, discount_percent, tax_percent):
    hundred = Decimal("100")
    gross = qty * rate
    discount_amt = gross * (discount_percent / hundred)
    basic = gross - discount_amt
    gst = basic * (tax_percent / hundred)
    return basic, gst, basic + gst


class ExpenseLineSerializer(serializers.Serializer):
    """Single purchase expense line row stored in PurchaseExpense.items_data."""

    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    product = serializers.IntegerField()
    product_name = serializers.CharField(read_only=True)
    unit = serializers.IntegerField()
    unit_name = serializers.CharField(read_only=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_type = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    discount_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    tax_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    basic = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    gst = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        if attrs["discount_percent"] < 0:
            raise serializers.ValidationError({"discount_percent": "Discount cannot be negative."})
        return attrs


class PurchaseExpenseListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    expense_number = serializers.CharField()
    expense_date = serializers.DateField()
    company_name = serializers.CharField()
    project_name = serializers.CharField(allow_blank=True)
    supplier_name = serializers.CharField(allow_blank=True)
    expense_category_name = serializers.CharField(allow_blank=True)
    expense_sub_category_name = serializers.CharField(allow_blank=True)
    payment_type_name = serializers.CharField(allow_blank=True)
    from_company = serializers.BooleanField()
    basic_amount = serializers.CharField()
    total_gst = serializers.CharField()
    round_off = serializers.CharField()
    total_amount = serializers.CharField()
    status = serializers.CharField()


class PurchaseExpenseSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    supplier_name = serializers.SerializerMethodField(read_only=True)
    items = ExpenseLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = PurchaseExpense
        fields = [
            "id",
            "unique_id",
            "expense_number",
            "expense_date",
            "company",
            "company_name",
            "project",
            "project_name",
            "supplier",
            "supplier_name",
            "supplier_manual_entry",
            "manual_supplier_name",
            "expense_category_id",
            "expense_category_name",
            "expense_sub_category_id",
            "expense_sub_category_name",
            "payment_type_id",
            "payment_type_name",
            "from_company",
            "remarks",
            "status",
            "level2_status",
            "items",
            "basic_amount",
            "total_gst",
            "round_off",
            "total_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "expense_number",
            "company_name",
            "project_name",
            "supplier_name",
            "basic_amount",
            "total_gst",
            "total_amount",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_alias = _masters_db_alias()
        field_querysets = {
            "company": CompanyMaster.objects.using(db_alias).filter(is_active=True),
            "project": ProjectMaster.objects.using(db_alias).filter(is_active=True),
        }
        for field_name, queryset in field_querysets.items():
            field = self.fields.get(field_name)
            if field is not None and hasattr(field, "queryset"):
                field.queryset = queryset

    def get_supplier_name(self, obj):
        if obj.supplier_manual_entry and obj.manual_supplier_name:
            return obj.manual_supplier_name
        return obj.supplier.name if obj.supplier else ""

    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
        project = attrs.get("project") or getattr(self.instance, "project", None)
        items = attrs.get("items_data")
        manual_flag = attrs.get(
            "supplier_manual_entry",
            getattr(self.instance, "supplier_manual_entry", False),
        )
        manual_name = attrs.get(
            "manual_supplier_name",
            getattr(self.instance, "manual_supplier_name", None),
        )
        supplier = attrs.get("supplier") or getattr(self.instance, "supplier", None)

        if company and project and project.company_id != company.id:
            raise serializers.ValidationError(
                {"project": "Selected project does not belong to the selected company."}
            )

        if not manual_flag and supplier is None:
            raise serializers.ValidationError(
                {"supplier": "Supplier is required unless manual entry is enabled."}
            )

        if manual_flag and not manual_name:
            raise serializers.ValidationError(
                {"manual_supplier_name": "Manual supplier name is required."}
            )

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one expense row is required."}
            )

        if items is not None and not items:
            raise serializers.ValidationError(
                {"items": "At least one expense row is required."}
            )

        return attrs

    def _normalise_items(self, items_data):
        rows = []
        total_basic = Decimal("0.00")
        total_gst = Decimal("0.00")

        for index, item_data in enumerate(items_data, start=1):
            product = _get_product(item_data["product"])
            unit = _get_unit(item_data["unit"])

            qty = _as_decimal(item_data["qty"])
            rate = _as_decimal(item_data["rate"])
            discount_percent = _as_decimal(item_data.get("discount_percent", "0"))
            tax_percent = _as_decimal(item_data.get("tax_percent", "0"))

            basic, gst, amount = _calculate_item_amounts(qty, rate, discount_percent, tax_percent)

            rows.append(
                {
                    "id": _line_id(item_data, index),
                    "unique_id": _line_unique_id(item_data),
                    "product": product.pk,
                    "product_name": product.product_name,
                    "unit": unit.pk,
                    "unit_name": unit.unit_name,
                    "qty": _decimal_to_str(qty),
                    "rate": _decimal_to_str(rate),
                    "discount_type": item_data.get("discount_type") or "",
                    "discount_percent": _decimal_to_str(discount_percent),
                    "tax_percent": _decimal_to_str(tax_percent),
                    "basic": _decimal_to_str(basic),
                    "gst": _decimal_to_str(gst),
                    "amount": _decimal_to_str(amount),
                    "remarks": item_data.get("remarks") or "",
                }
            )

            total_basic += basic
            total_gst += gst

        return rows, total_basic, total_gst

    def _save_totals(self, expense, stored_items, total_basic, total_gst):
        round_off = _as_decimal(expense.round_off)
        total_amount = total_basic + total_gst + round_off

        expense.items_data = stored_items
        expense.basic_amount = total_basic
        expense.total_gst = total_gst
        expense.total_amount = total_amount
        expense.save(
            update_fields=[
                "items_data",
                "basic_amount",
                "total_gst",
                "total_amount",
                "updated_at",
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data", [])
        company = validated_data.get("company")
        project = validated_data.get("project")
        if company is not None:
            validated_data["company"] = _sync_local_company(company)
        if project is not None:
            validated_data["project"] = _sync_local_project(project)

        expense = PurchaseExpense.objects.create(**validated_data)
        stored_items, total_basic, total_gst = self._normalise_items(items_data)
        self._save_totals(expense, stored_items, total_basic, total_gst)
        return expense

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        company = validated_data.get("company")
        project = validated_data.get("project")
        if company is not None:
            validated_data["company"] = _sync_local_company(company)
        if project is not None:
            validated_data["project"] = _sync_local_project(project)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is None:
            stored_items = instance.items_data or []
            total_basic = sum((_as_decimal(i.get("basic")) for i in stored_items), Decimal("0.00"))
            total_gst = sum((_as_decimal(i.get("gst")) for i in stored_items), Decimal("0.00"))
        else:
            stored_items, total_basic, total_gst = self._normalise_items(items_data)

        self._save_totals(instance, stored_items, total_basic, total_gst)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        raw_items = instance.items_data if isinstance(instance.items_data, list) else []
        representation["items"] = raw_items
        return representation
