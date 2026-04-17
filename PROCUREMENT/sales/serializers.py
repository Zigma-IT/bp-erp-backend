"""Serializers for sales, invoice, ordered BOM, and expense endpoints."""

import uuid
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from purchase_master.models import Category, ItemGroup, ProductCreation, SubGroup, UnitMaster

from .models import ExpenseEntry, OrderedBOM, SalesInvoice, SalesOrder


def _as_decimal(value, default="0.00"):
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def _decimal_to_json(value):
    return str(_as_decimal(value))


def _line_id(item_data, index):
    return item_data.get("id") or index


def _line_unique_id(item_data):
    return str(item_data.get("unique_id") or uuid.uuid4())


def _get_product(product_id):
    product = ProductCreation.objects.select_related("company").filter(pk=product_id).first()
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


def _get_group(group_id):
    group = ItemGroup.objects.filter(pk=group_id).first()
    if group is None:
        raise serializers.ValidationError({"items": f"Group id {group_id} was not found."})
    return group


def _get_sub_group(sub_group_id):
    sub_group = SubGroup.objects.filter(pk=sub_group_id).first()
    if sub_group is None:
        raise serializers.ValidationError(
            {"items": f"Sub group id {sub_group_id} was not found."}
        )
    return sub_group


def _get_category(category_id):
    category = Category.objects.filter(pk=category_id).first()
    if category is None:
        raise serializers.ValidationError(
            {"items": f"Category id {category_id} was not found."}
        )
    return category


def _calculate_commercial_line(item_data):
    qty = _as_decimal(item_data["qty"])
    rate = _as_decimal(item_data["rate"])
    discount = _as_decimal(item_data.get("discount_percent"))
    tax = _as_decimal(item_data.get("tax_percent"))

    base = qty * rate
    discount_amount = base * (discount / Decimal("100"))
    net = base - discount_amount
    tax_amount = net * (tax / Decimal("100"))
    return net, tax_amount, net + tax_amount


# >>>>>>>>>>>>>>>>>>>>>>>>>>> Sales Invoice >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class SalesInvoiceLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    invoice = serializers.IntegerField(required=False, allow_null=True)
    product = serializers.IntegerField()
    product_name = serializers.CharField(read_only=True)
    unit = serializers.IntegerField()
    uom = serializers.CharField(read_only=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        _get_product(attrs["product"])
        _get_unit(attrs["unit"])
        return attrs


class SalesInvoiceSerializer(serializers.ModelSerializer):
    items = SalesInvoiceLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = SalesInvoice
        fields = [
            "id",
            "unique_id",
            "entry_date",
            "due_date",
            "company",
            "project",
            "customer",
            "invoice_number",
            "remarks",
            "basic_amount",
            "total_gst",
            "round_off",
            "total_amount",
            "status",
            "created_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "invoice_number",
            "basic_amount",
            "total_gst",
            "total_amount",
            "created_at",
        ]

    def validate(self, attrs):
        items = attrs.get("items_data")
        company = attrs.get("company") or getattr(self.instance, "company", None)

        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "At least one invoice row is required."})
        if items is not None and not items:
            raise serializers.ValidationError({"items": "At least one invoice row is required."})

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
        return attrs

    def _normalise_items(self, items_data, invoice=None):
        rows = []
        basic = Decimal("0.00")
        gst_total = Decimal("0.00")

        for index, item in enumerate(items_data, start=1):
            product = _get_product(item["product"])
            unit = _get_unit(item["unit"])
            net, tax_amount, total = _calculate_commercial_line(item)
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "invoice": invoice.pk if invoice and invoice.pk else item.get("invoice"),
                    "product": product.pk,
                    "product_name": product.product_name,
                    "unit": unit.pk,
                    "uom": unit.unit_name,
                    "qty": _decimal_to_json(item["qty"]),
                    "rate": _decimal_to_json(item["rate"]),
                    "discount_type": item.get("discount_type") or "",
                    "discount_percent": _decimal_to_json(item.get("discount_percent")),
                    "tax_percent": _decimal_to_json(item.get("tax_percent")),
                    "amount": _decimal_to_json(total),
                    "remarks": item.get("remarks") or "",
                }
            )
            basic += net
            gst_total += tax_amount

        return rows, basic, gst_total

    def _stored_totals(self, stored_items):
        basic = Decimal("0.00")
        gst_total = Decimal("0.00")
        for item in stored_items:
            net, tax_amount, _total = _calculate_commercial_line(item)
            basic += net
            gst_total += tax_amount
        return basic, gst_total

    def _save_amounts(self, invoice, stored_items, basic, gst_total):
        invoice.items_data = stored_items
        invoice.basic_amount = basic
        invoice.total_gst = gst_total
        invoice.total_amount = basic + gst_total + invoice.round_off
        invoice.save(
            update_fields=[
                "items_data",
                "basic_amount",
                "total_gst",
                "total_amount",
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        invoice = SalesInvoice.objects.create(**validated_data)
        stored_items, basic, gst_total = self._normalise_items(items_data, invoice)
        self._save_amounts(invoice, stored_items, basic, gst_total)
        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is None:
            stored_items = instance.items_data or []
            basic, gst_total = self._stored_totals(stored_items)
        else:
            stored_items, basic, gst_total = self._normalise_items(items_data, instance)
        self._save_amounts(instance, stored_items, basic, gst_total)
        return instance


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
            queryset = ProductCreation.objects.all()
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
    items = SalesOrderLineSerializer(many=True, source="items_data", required=False)

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
        items_data = validated_data.pop("items_data")
        sales_order = SalesOrder.objects.create(**validated_data)
        sales_order.items_data = self._normalise_items(items_data)
        sales_order.save(update_fields=["items_data"])
        return sales_order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Ordered BOM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class OrderedBOMLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    group = serializers.IntegerField()
    group_name = serializers.CharField(read_only=True)
    sub_group = serializers.IntegerField()
    sub_group_name = serializers.CharField(read_only=True)
    category = serializers.IntegerField()
    category_name = serializers.CharField(read_only=True)
    item = serializers.IntegerField()
    item_name = serializers.CharField(read_only=True)
    unit = serializers.IntegerField()
    uom = serializers.CharField(read_only=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(default="active")

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        _get_group(attrs["group"])
        _get_sub_group(attrs["sub_group"])
        _get_category(attrs["category"])
        _get_product(attrs["item"])
        _get_unit(attrs["unit"])
        return attrs


class OrderedBOMSerializer(serializers.ModelSerializer):
    items = OrderedBOMLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = OrderedBOM
        fields = [
            "id",
            "unique_id",
            "company",
            "sales_order",
            "so_type",
            "material_type",
            "created_at",
            "items",
        ]
        read_only_fields = ["id", "unique_id", "created_at"]

    def validate(self, attrs):
        items = attrs.get("items_data")
        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "At least one BOM row is required."})
        if items is not None and not items:
            raise serializers.ValidationError({"items": "At least one BOM row is required."})
        return attrs

    def _normalise_items(self, items_data):
        rows = []
        for index, item in enumerate(items_data, start=1):
            group = _get_group(item["group"])
            sub_group = _get_sub_group(item["sub_group"])
            category = _get_category(item["category"])
            product = _get_product(item["item"])
            unit = _get_unit(item["unit"])
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "group": group.pk,
                    "group_name": group.group_name,
                    "sub_group": sub_group.pk,
                    "sub_group_name": sub_group.sub_group_name,
                    "category": category.pk,
                    "category_name": category.category_name,
                    "item": product.pk,
                    "item_name": product.product_name,
                    "unit": unit.pk,
                    "uom": unit.unit_name,
                    "qty": _decimal_to_json(item["qty"]),
                    "remarks": item.get("remarks") or "",
                    "status": item.get("status") or "active",
                }
            )
        return rows

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        bom = OrderedBOM.objects.create(**validated_data)
        bom.items_data = self._normalise_items(items_data)
        bom.save(update_fields=["items_data"])
        return bom

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if items_data is not None:
            instance.items_data = self._normalise_items(items_data)
        instance.save()
        return instance


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Purchase Expense >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class ExpenseLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    unique_id = serializers.UUIDField(required=False)
    product = serializers.IntegerField()
    product_name = serializers.CharField(read_only=True)
    unit = serializers.IntegerField()
    uom = serializers.CharField(read_only=True)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than zero."})
        if attrs["rate"] < 0:
            raise serializers.ValidationError({"rate": "Rate cannot be negative."})
        _get_product(attrs["product"])
        _get_unit(attrs["unit"])
        return attrs


class ExpenseEntrySerializer(serializers.ModelSerializer):
    items = ExpenseLineSerializer(many=True, source="items_data", required=False)

    class Meta:
        model = ExpenseEntry
        fields = [
            "id",
            "unique_id",
            "company",
            "project",
            "supplier",
            "manual_supplier_name",
            "payment_type",
            "expense_date",
            "expense_number",
            "remarks",
            "basic_amount",
            "total_gst",
            "round_off",
            "total_amount",
            "status",
            "created_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "unique_id",
            "expense_number",
            "basic_amount",
            "total_gst",
            "total_amount",
            "created_at",
        ]

    def validate(self, attrs):
        items = attrs.get("items_data")
        company = attrs.get("company") or getattr(self.instance, "company", None)

        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "At least one expense row is required."})
        if items is not None and not items:
            raise serializers.ValidationError({"items": "At least one expense row is required."})

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
        return attrs

    def _normalise_items(self, items_data):
        rows = []
        basic = Decimal("0.00")
        gst_total = Decimal("0.00")

        for index, item in enumerate(items_data, start=1):
            product = _get_product(item["product"])
            unit = _get_unit(item["unit"])
            net, tax_amount, total = _calculate_commercial_line(item)
            rows.append(
                {
                    "id": _line_id(item, index),
                    "unique_id": _line_unique_id(item),
                    "product": product.pk,
                    "product_name": product.product_name,
                    "unit": unit.pk,
                    "uom": unit.unit_name,
                    "qty": _decimal_to_json(item["qty"]),
                    "rate": _decimal_to_json(item["rate"]),
                    "discount_type": item.get("discount_type") or "",
                    "discount_percent": _decimal_to_json(item.get("discount_percent")),
                    "tax_percent": _decimal_to_json(item.get("tax_percent")),
                    "amount": _decimal_to_json(total),
                    "remarks": item.get("remarks") or "",
                }
            )
            basic += net
            gst_total += tax_amount

        return rows, basic, gst_total

    def _stored_totals(self, stored_items):
        basic = Decimal("0.00")
        gst_total = Decimal("0.00")
        for item in stored_items:
            net, tax_amount, _total = _calculate_commercial_line(item)
            basic += net
            gst_total += tax_amount
        return basic, gst_total

    def _save_amounts(self, expense_entry, stored_items, basic, gst_total):
        expense_entry.items_data = stored_items
        expense_entry.basic_amount = basic
        expense_entry.total_gst = gst_total
        expense_entry.total_amount = basic + gst_total + expense_entry.round_off
        expense_entry.save(
            update_fields=[
                "items_data",
                "basic_amount",
                "total_gst",
                "total_amount",
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items_data")
        obj = ExpenseEntry.objects.create(**validated_data)
        stored_items, basic, gst_total = self._normalise_items(items_data)
        self._save_amounts(obj, stored_items, basic, gst_total)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items_data", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is None:
            stored_items = instance.items_data or []
            basic, gst_total = self._stored_totals(stored_items)
        else:
            stored_items, basic, gst_total = self._normalise_items(items_data)
        self._save_amounts(instance, stored_items, basic, gst_total)
        return instance


# >>>>>>>>>>>>>>>>>>>>>>>>>>>> Purchase Expense Approval <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class ExpenseApprovalActionSerializer(serializers.Serializer):
    expense_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    remarks = serializers.CharField(required=False)
