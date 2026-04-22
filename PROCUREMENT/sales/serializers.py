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
        model = SalesOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit",
            "uom",
            "qty",
            "rate",
            "tax_percent",
            "amount",
            "sub_task",
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


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = '__all__'
        read_only_fields = ['id', 'so_number', 'created_at']

    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
        items = attrs.get("items")

        if self.instance is None and not items:
            raise serializers.ValidationError(
                {"items": "At least one sales-order row is required."}
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
        so = SalesOrder.objects.create(**validated_data)

        hundred = Decimal("100")

        for item in items_data:
            qty = item["qty"]
            rate = item["rate"]
            tax = item.get("tax_percent", Decimal("0"))

            base = qty * rate
            tax_amt = base * (tax / hundred)
            amount = base + tax_amt

            SalesOrderItem.objects.create(
                sales_order=so,
                amount=amount,
                **item,
            )

        return so

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

                base = qty * rate
                tax_amt = base * (tax / hundred)
                amount = base + tax_amt

                SalesOrderItem.objects.create(
                    sales_order=instance,
                    amount=amount,
                    **item,
                )

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
