"""Tests for the sales app serializers and ordered BOM validation."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from .serializers import OrderedBOMSerializer


class OrderedBOMSerializerTests(TestCase):
    @patch("sales.serializers.SalesOrder.objects.get")
    def test_ordered_bom_serializer_infers_company_from_sales_order(self, mock_get):
        mock_sales_order = SimpleNamespace(id=7, company=SimpleNamespace(id=5))
        mock_get.return_value = mock_sales_order

        serializer = OrderedBOMSerializer(
            data={
                "sales_order": 7,
                "material_type": "with_material",
                "items": [],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["company"].id, 5)
