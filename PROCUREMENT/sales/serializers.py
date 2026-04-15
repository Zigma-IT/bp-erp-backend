from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import ProductMaster, SalesOrder, SalesOrderItem, UnitMaster


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
