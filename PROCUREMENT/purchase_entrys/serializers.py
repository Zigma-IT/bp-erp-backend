from decimal import Decimal

from rest_framework import serializers
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id',
            'product_name',
            'uom',
            'qty',
            'rate',
            'discount_percent',
            'tax_percent',
            'amount',
            'delivery_date',
            'remarks',
        ]
        read_only_fields = ['id', 'amount']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id',
            'po_number',
            'company',
            'project',
            'supplier',
            'entry_date',
            'quotation_no',
            'quotation_date',
            'revision_no',
            'revision_date',
            'revision_remarks',
            'total_basic_value',
            'freight_charges',
            'other_charges',
            'packing_charges',
            'round_off',
            'total_gst',
            'gross_amount',
            'status',
            'created_at',
            'items',
        ]
        read_only_fields = ['id', 'total_basic_value', 'total_gst', 'gross_amount', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        po = PurchaseOrder.objects.create(**validated_data)

        total_basic = Decimal('0.00')
        total_gst = Decimal('0.00')
        hundred = Decimal('100')

        for item in items_data:
            qty = item['qty']
            rate = item['rate']
            discount = item.get('discount_percent', Decimal('0.00'))
            tax = item.get('tax_percent', Decimal('0.00'))

            base = qty * rate
            discount_amt = base * (discount / hundred)
            taxable = base - discount_amt
            gst_amt = taxable * (tax / hundred)

            amount = taxable + gst_amt

            total_basic += taxable
            total_gst += gst_amt

            PurchaseOrderItem.objects.create(
                purchase_order=po,
                amount=amount,
                **item
            )

        po.total_basic_value = total_basic
        po.total_gst = total_gst
        po.gross_amount = (
            total_basic +
            total_gst +
            po.freight_charges +
            po.other_charges +
            po.packing_charges +
            po.round_off
        )
        po.save()

        return po
