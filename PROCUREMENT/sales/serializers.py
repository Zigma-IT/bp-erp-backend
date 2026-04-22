"""Serializers for sales, invoice, ordered BOM, and expense endpoints."""

import uuid
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import (
    ProductMaster,
    PurchaseExpense,
    PurchaseExpenseItem,
    SalesOrder,
    SalesOrderItem,
    SalesInvoice,
    SalesInvoiceItem,
    UnitMaster,
)


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    uom = serializers.CharField(source="unit.unit_name", read_only=True)

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


# Sales Invoice
class SalesInvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    uom = serializers.CharField(source="unit.unit_name", read_only=True)

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
    items = SalesInvoiceItemSerializer(many=True)

    class Meta:
        model = SalesInvoice
        fields = "__all__"
        read_only_fields = ["id", "invoice_number", "created_at"]

    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
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

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        invoice = SalesInvoice.objects.create(**validated_data)

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


class PurchaseExpenseSerializer(serializers.ModelSerializer):
    items = PurchaseExpenseItemSerializer(many=True)
    supplier_name = serializers.SerializerMethodField(read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    category_name = serializers.CharField(source="category.group_name", read_only=True)
    sub_category_name = serializers.CharField(source="sub_category.sub_group_name", read_only=True)

    class Meta:
        model = PurchaseExpense
        fields = "__all__"
        read_only_fields = ["id", "expense_number", "created_at", "supplier_name", "project_name", "category_name", "sub_category_name"]

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
