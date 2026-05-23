"""Serializers for sales, invoice, ordered BOM, and expense endpoints."""

import uuid
from decimal import Decimal

from django.db import connections
from django.db import transaction
from rest_framework import serializers

from .models import (
    PurchaseExpense,
    PurchaseExpenseItem,
    Customer,
    SalesOrder,
    SalesInvoice,
    SalesInvoiceItem,
)
from common_master.models import Company as CompanyMaster
from common_master.models import CustomerProfile as CustomerMaster
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import UnitMaster


def _masters_db_alias():
    return "masters_db" if "masters_db" in connections.databases else "default"


def _as_decimal(value):
    if value in (None, ""):
        return Decimal("0.00")
    return Decimal(str(value))


def _line_id(item, fallback):
    return item.get("id") or fallback


def _line_unique_id(item):
    value = item.get("unique_id")
    return str(value) if value else str(uuid.uuid4())


def _decimal_to_json(value):
    return str(_as_decimal(value))


def _belongs_to_company(product, company):
    return product.company_id == company.id


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


def _get_customer(customer_id):
    try:
        return CustomerMaster.objects.using(_masters_db_alias()).get(
            pk=customer_id,
            is_delete=False,
            is_active=True,
        )
    except CustomerMaster.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"customer": f"Invalid customer id '{customer_id}'."}
        ) from exc


# >>>>>>>>>>>>>>>>>>>>>>>>>>> Sales Order >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class SalesOrderLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    product = serializers.IntegerField(required=False, allow_null=True)
    product_name = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.IntegerField(required=False, allow_null=True)
    uom = serializers.CharField(required=False, allow_blank=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    sub_task = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def to_internal_value(self, data):
        mutable_data = data.copy()
        company_id = None

        parent = getattr(self, "parent", None)
        root_serializer = getattr(parent, "parent", None)
        if root_serializer is not None:
            company_id = root_serializer.initial_data.get("company")

        if not mutable_data.get("product") and mutable_data.get("product_name"):
            queryset = ProductMaster.objects.all()
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            product = queryset.filter(product_name=mutable_data["product_name"]).first()
            if product is None:
                raise serializers.ValidationError(
                    {"product_name": "Matching product was not found in MASTERS."}
                )
            mutable_data["product"] = product.pk

        if not mutable_data.get("unit") and mutable_data.get("uom"):
            unit = UnitMaster.objects.filter(unit_name=mutable_data["uom"]).first()
            if unit is None:
                raise serializers.ValidationError(
                    {"uom": "Matching unit was not found in MASTERS."}
                )
            mutable_data["unit"] = unit.pk

        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        if not attrs.get("product"):
            raise serializers.ValidationError({"product": "Product is required."})
        if not attrs.get("unit"):
            raise serializers.ValidationError({"unit": "Unit is required."})
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        _get_product(attrs["product"])
        _get_unit(attrs["unit"])
        return attrs


class SalesOrderSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=CompanyMaster.objects.none())
    customer = serializers.IntegerField(source="customer_id")
    items = SalesOrderLineSerializer(many=True, source="items_data", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_alias = _masters_db_alias()
        self.fields["company"].queryset = CompanyMaster.objects.using(db_alias).all()

    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "unique_id",
            "entry_date",
            "company",
            "customer",
            "so_number",
            "so_type",
            "currency",
            "exchange_rate",
            "contact_person",
            "customer_po_number",
            "customer_po_date",
            "active_status",
            "status",
            "created_at",
            "items",
        ]
        read_only_fields = ["id", "unique_id", "so_number", "created_at"]

    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
        customer_id = attrs.get("customer_id", getattr(self.instance, "customer_id", None))
        items = attrs.get("items_data")

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one sales-order row is required."}
            )
        if items is not None and not items:
            raise serializers.ValidationError(
                {"items": "At least one sales-order row is required."}
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

        if customer_id:
            _get_customer(customer_id)

        return attrs

    def _normalise_items(self, items_data):
        rows = []
        for index, item in enumerate(items_data, start=1):
            product = _get_product(item["product"])
            unit = _get_unit(item["unit"])
            qty = _as_decimal(item["qty"])
            rate = _as_decimal(item["rate"])
            tax = _as_decimal(item.get("tax_percent"))
            base = qty * rate
            tax_amount = base * (tax / Decimal("100"))
            amount = base + tax_amount

            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "product": product.pk,
                    "product_name": product.product_name,
                    "unit": unit.pk,
                    "uom": unit.unit_name,
                    "qty": _decimal_to_json(qty),
                    "rate": _decimal_to_json(rate),
                    "tax_percent": _decimal_to_json(tax),
                    "amount": _decimal_to_json(amount),
                    "sub_task": item.get("sub_task") or "",
                }
            )
        return rows

    @transaction.atomic
    def create(self, validated_data):
        customer_id = validated_data.pop("customer_id")
        items_data = validated_data.pop("items_data")
        sales_order = SalesOrder.objects.create(customer_id=customer_id, **validated_data)
        sales_order.items_data = self._normalise_items(items_data)
        sales_order.save(update_fields=["items_data"])
        return sales_order

    @transaction.atomic
    def update(self, instance, validated_data):
        customer_id = validated_data.pop("customer_id", None)
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if customer_id is not None:
            instance.customer_id = customer_id
        if items_data is not None:
            instance.items_data = self._normalise_items(items_data)
        instance.save()
        return instance


class SalesOrderListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    entry_date = serializers.DateField()
    sales_order_no = serializers.CharField()
    company_name = serializers.CharField()
    customer_name = serializers.CharField()
    so_type = serializers.CharField()
    active_status = serializers.CharField()
    approve_status = serializers.CharField()


# Sales Invoice
class SalesInvoiceItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=ProductMaster.objects.none())
    unit = serializers.PrimaryKeyRelatedField(queryset=UnitMaster.objects.none())
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    uom = serializers.CharField(source="unit.unit_name", read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_alias = _masters_db_alias()
        self.fields["product"].queryset = ProductMaster.objects.using(db_alias).all()
        self.fields["unit"].queryset = UnitMaster.objects.using(db_alias).all()

    class Meta:
        model = SalesInvoiceItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit",
            "uom",
            "qty",
            "rate",
            "discount_type",
            "discount_percent",
            "tax_percent",
            "amount",
            "remarks",
        ]
        read_only_fields = ["id", "product_name", "uom", "amount"]

    def to_internal_value(self, data):
        mutable_data = data.copy()
        company_id = None

        parent = getattr(self, "parent", None)
        root_serializer = getattr(parent, "parent", None)
        if root_serializer is not None:
            company_id = root_serializer.initial_data.get("company")

        if not mutable_data.get("product") and mutable_data.get("product_name"):
            queryset = ProductMaster.objects.all()
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            product = queryset.filter(product_name=mutable_data["product_name"]).first()
            if product is None:
                raise serializers.ValidationError(
                    {"product_name": "Matching product was not found in MASTERS."}
                )
            mutable_data["product"] = product.pk

        if not mutable_data.get("unit") and mutable_data.get("uom"):
            unit = UnitMaster.objects.filter(unit_name=mutable_data["uom"]).first()
            if unit is None:
                raise serializers.ValidationError(
                    {"uom": "Matching unit was not found in MASTERS."}
                )
            mutable_data["unit"] = unit.pk

        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        if attrs.get("product") is None:
            raise serializers.ValidationError({"product": "Product is required."})
        if attrs.get("unit") is None:
            raise serializers.ValidationError({"unit": "Unit is required."})
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        return attrs


class SalesInvoiceSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=CompanyMaster.objects.none())
    customer = serializers.IntegerField(source="customer_id")
    project = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    items = SalesInvoiceItemSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_alias = _masters_db_alias()
        self.fields["company"].queryset = CompanyMaster.objects.using(db_alias).all()

    class Meta:
        model = SalesInvoice
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        attrs.pop("project", None)
        company = attrs.get("company") or getattr(self.instance, "company", None)
        customer_id = attrs.get("customer_id", getattr(self.instance, "customer_id", None))
        items = attrs.get("items")

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one invoice row is required."}
            )

        if items and company:
            for item in items:
                product = item.get("product")
                if product and product.company_id != company.id:
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"Product '{product.product_name}' does not belong to "
                                f"company '{company.name}'."
                            )
                        }
                    )

        if customer_id:
            _get_customer(customer_id)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("project", None)
        customer_id = validated_data.pop("customer_id")
        items_data = validated_data.pop("items")
        invoice = SalesInvoice.objects.create(customer_id=customer_id, **validated_data)

        hundred = Decimal("100")

        for item in items_data:
            qty = item["qty"]
            rate = item["rate"]
            tax = item.get("tax_percent", Decimal("0"))
            discount = item.get("discount_percent", Decimal("0"))

            base = qty * rate
            discount_amt = base * (discount / hundred)
            discounted_base = base - discount_amt
            tax_amt = discounted_base * (tax / hundred)
            amount = discounted_base + tax_amt

            SalesInvoiceItem.objects.create(
                sales_invoice=invoice,
                amount=amount,
                **item,
            )

        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop("project", None)
        customer_id = validated_data.pop("customer_id", None)
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if customer_id is not None:
            instance.customer_id = customer_id
        instance.save()

        if items_data is not None:
            instance.items.all().delete()

            hundred = Decimal("100")
            for item in items_data:
                qty = item["qty"]
                rate = item["rate"]
                tax = item.get("tax_percent", Decimal("0"))
                discount = item.get("discount_percent", Decimal("0"))

                base = qty * rate
                discount_amt = base * (discount / hundred)
                discounted_base = base - discount_amt
                tax_amt = discounted_base * (tax / hundred)
                amount = discounted_base + tax_amt

                SalesInvoiceItem.objects.create(
                    sales_invoice=instance,
                    amount=amount,
                    **item,
                )

        return instance


class SalesInvoiceListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    invoice_date = serializers.DateField()
    invoice_number = serializers.CharField()
    company_name = serializers.CharField()
    customer_name = serializers.CharField()
    amount = serializers.CharField()
    approve_status = serializers.CharField()


class PurchaseExpenseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    uom = serializers.CharField(source="unit.unit_name", read_only=True)

    class Meta:
        model = PurchaseExpenseItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit",
            "uom",
            "qty",
            "rate",
            "discount_type",
            "discount_percent",
            "tax_percent",
            "amount",
            "remarks",
        ]
        read_only_fields = ["id", "product_name", "uom", "amount"]

    def to_internal_value(self, data):
        mutable_data = data.copy()
        company_id = None

        parent = getattr(self, "parent", None)
        root_serializer = getattr(parent, "parent", None)
        if root_serializer is not None:
            company_id = root_serializer.initial_data.get("company")

        if not mutable_data.get("product") and mutable_data.get("product_name"):
            queryset = ProductMaster.objects.using(_masters_db_alias()).all()
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            product = queryset.filter(product_name=mutable_data["product_name"]).first()
            if product is None:
                raise serializers.ValidationError(
                    {"product_name": "Matching product was not found in MASTERS."}
                )
            mutable_data["product"] = product.pk

        if not mutable_data.get("unit") and mutable_data.get("uom"):
            unit = (
                UnitMaster.objects.using(_masters_db_alias())
                .filter(unit_name=mutable_data["uom"])
                .first()
            )
            if unit is None:
                raise serializers.ValidationError(
                    {"uom": "Matching unit was not found in MASTERS."}
                )
            mutable_data["unit"] = unit.pk

        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        if attrs.get("product") is None:
            raise serializers.ValidationError({"product": "Product is required."})
        if attrs.get("unit") is None:
            raise serializers.ValidationError({"unit": "Unit is required."})
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        return attrs


class PurchaseExpenseSerializer(serializers.ModelSerializer):
    items = PurchaseExpenseItemSerializer(many=True)
    supplier_name = serializers.SerializerMethodField(read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    category_name = serializers.CharField(source="category.group_name", read_only=True)
    sub_category_name = serializers.CharField(source="sub_category.sub_group_name", read_only=True)

    class Meta:
        model = PurchaseExpense
        fields = "__all__"
        read_only_fields = ["id", "created_at", "supplier_name", "project_name", "category_name", "sub_category_name"]

    def get_supplier_name(self, obj):
        if obj.supplier_manual_entry and obj.manual_supplier_name:
            return obj.manual_supplier_name
        return obj.supplier.name if obj.supplier else ""

    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
        items = attrs.get("items")
        supplier = attrs.get("supplier") or getattr(self.instance, "supplier", None)
        manual_flag = attrs.get("supplier_manual_entry", getattr(self.instance, "supplier_manual_entry", False))
        manual_name = attrs.get("manual_supplier_name", getattr(self.instance, "manual_supplier_name", None))

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one expense row is required."}
            )

        if not manual_flag and supplier is None:
            raise serializers.ValidationError({"supplier": "Supplier is required unless manual entry is enabled."})

        if manual_flag and not manual_name:
            raise serializers.ValidationError({"manual_supplier_name": "Manual supplier name is required."})

        if items and company:
            for item in items:
                product = item.get("product")
                if product and product.company_id != company.id:
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"Product '{product.product_name}' does not belong to "
                                f"company '{company.name}'."
                            )
                        }
                    )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        expense = PurchaseExpense.objects.create(**validated_data)

        hundred = Decimal("100")
        for item in items_data:
            qty = item["qty"]
            rate = item["rate"]
            tax = item.get("tax_percent", Decimal("0"))
            discount = item.get("discount_percent", Decimal("0"))

            base = qty * rate
            discount_amt = base * (discount / hundred)
            discounted_base = base - discount_amt
            tax_amt = discounted_base * (tax / hundred)
            amount = discounted_base + tax_amt

            PurchaseExpenseItem.objects.create(
                purchase_expense=expense,
                amount=amount,
                **item,
            )

        return expense

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()

            hundred = Decimal("100")
            for item in items_data:
                qty = item["qty"]
                rate = item["rate"]
                tax = item.get("tax_percent", Decimal("0"))
                discount = item.get("discount_percent", Decimal("0"))

                base = qty * rate
                discount_amt = base * (discount / hundred)
                discounted_base = base - discount_amt
                tax_amt = discounted_base * (tax / hundred)
                amount = discounted_base + tax_amt

                PurchaseExpenseItem.objects.create(
                    purchase_expense=instance,
                    amount=amount,
                    **item,
                )

        return instance


class PurchaseExpenseListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    expense_date = serializers.DateField()
    expense_number = serializers.CharField()
    company_name = serializers.CharField()
    project_name = serializers.CharField(allow_blank=True)
    category_name = serializers.CharField(allow_blank=True)
    sub_category_name = serializers.CharField(allow_blank=True)
    payment_type = serializers.CharField()
    supplier_name = serializers.CharField(allow_blank=True)
    total_amount = serializers.CharField()
    approval_status = serializers.CharField()
