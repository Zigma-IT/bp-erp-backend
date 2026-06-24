#!/usr/bin/env python3
"""Verify that purchase_entrys has been moved to business-code references."""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from purchase_entrys.scripts._runtime import find_repo_root
from django.db.utils import OperationalError


def _setup_django() -> None:
    repo_root = find_repo_root()
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PROCUREMENT.settings")

    import django

    django.setup()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _verify_model_fields(model, expected_fields, removed_fields):
    field_names = {field.name for field in model._meta.get_fields()}
    missing = sorted(set(expected_fields) - field_names)
    _assert(not missing, f"{model.__name__} is missing fields: {', '.join(missing)}")

    present_removed = sorted(set(removed_fields) & field_names)
    _assert(
        not present_removed,
        f"{model.__name__} still exposes legacy fields: {', '.join(present_removed)}",
    )


def _verify_non_empty_queryset(model, field_names):
    rows = list(model.objects.all().values_list("pk", *field_names))
    missing = [
        row[0]
        for row in rows
        if any(value in (None, "") for value in row[1:])
    ]
    _assert(
        not missing,
        f"{model.__name__} has rows with empty business-code fields: {missing[:10]}",
    )
    return len(rows)


def main() -> None:
    _setup_django()

    try:
        from purchase_entrys.models import (
            GRN,
            PurchaseOrder,
            PurchaseRequisition,
            RateOrder,
            SRN,
            SRNItem,
            Supplier,
        )

        _verify_model_fields(
            Supplier,
            expected_fields={"supplier_code", "name", "is_active"},
            removed_fields={"supplier"},
        )
        _verify_model_fields(
            RateOrder,
            expected_fields={"company_code", "project_code", "supplier_code", "supplier_name"},
            removed_fields={"company", "project", "supplier"},
        )
        _verify_model_fields(
            PurchaseOrder,
            expected_fields={
                "company_code",
                "project_code",
                "supplier_code",
                "supplier_name",
                "freight_tax_code",
                "other_tax_code",
                "packing_tax_code",
            },
            removed_fields={
                "company",
                "project",
                "supplier",
                "freight_tax",
                "other_tax",
                "packing_tax",
            },
        )
        _verify_model_fields(
            PurchaseRequisition,
            expected_fields={"company_code", "project_code"},
            removed_fields={"company", "project"},
        )
        _verify_model_fields(
            GRN,
            expected_fields={"company_code", "project_code", "supplier_code", "supplier_name"},
            removed_fields={"company", "project", "supplier"},
        )
        _verify_model_fields(
            SRN,
            expected_fields={"company_code", "project_code", "supplier_code", "supplier_name"},
            removed_fields={"company", "project", "supplier"},
        )
        _verify_model_fields(
            SRNItem,
            expected_fields={"item_code", "item_name"},
            removed_fields={"item"},
        )

        counts = Counter()
        counts["suppliers"] = _verify_non_empty_queryset(Supplier, ["supplier_code"])
        counts["rate_orders"] = _verify_non_empty_queryset(
            RateOrder, ["company_code", "project_code", "supplier_code"]
        )
        counts["purchase_orders"] = _verify_non_empty_queryset(
            PurchaseOrder,
            [
                "company_code",
                "project_code",
                "supplier_code",
                "freight_tax_code",
                "other_tax_code",
                "packing_tax_code",
            ],
        )
        counts["purchase_requisitions"] = _verify_non_empty_queryset(
            PurchaseRequisition, ["company_code", "project_code"]
        )
        counts["grns"] = _verify_non_empty_queryset(
            GRN, ["company_code", "project_code", "supplier_code"]
        )
        counts["srns"] = _verify_non_empty_queryset(
            SRN, ["company_code", "project_code", "supplier_code"]
        )
        counts["srn_items"] = _verify_non_empty_queryset(
            SRNItem, ["item_code", "item_name"]
        )
    except OperationalError as exc:
        raise SystemExit(f"Database connection unavailable for verification: {exc}") from exc

    print("purchase_entrys module-reference verification passed")
    for label, count in counts.items():
        print(f"{label}: {count} rows checked")


if __name__ == "__main__":
    main()
