"""Service-layer accessors for master data used by Procurement entries."""

from functools import lru_cache

from django.db import connections

from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from common_master.models import SupplierProfile as SupplierProfileMaster
from common_master.models import Tax as TaxMaster
from purchase_master.models import ItemMaster
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import UnitMaster

from .models import Supplier


MASTERS_DB_ALIAS = "masters_db1"


class MasterDataNotFound(Exception):
    """Raised when a requested master record cannot be resolved."""


def generated_supplier_code(supplier_id):
    if supplier_id is None:
        return None
    return f"SUP-{supplier_id:05d}"


class MasterDataService:
    """Centralized read access to master data for the Procurement module.

    The cached single-record helpers use small in-process LRU caches to avoid
    repeated lookups during serializer normalization. Queryset helpers are left
    uncached so dropdown filtering/searching always reflects current data.
    """

    db_alias = MASTERS_DB_ALIAS

    @classmethod
    def active_companies(cls):
        return CompanyMaster.objects.using(cls.db_alias).filter(is_active=True)

    @classmethod
    def active_projects(cls):
        return ProjectMaster.objects.using(cls.db_alias).filter(is_active=True)

    @classmethod
    def active_products(cls):
        return ProductMaster.objects.using(cls.db_alias).filter(is_active=True)

    @classmethod
    def active_items(cls):
        return ItemMaster.objects.using(cls.db_alias).filter(is_active=True)

    @classmethod
    def active_units(cls):
        return UnitMaster.objects.using(cls.db_alias).filter(is_active=True)

    @classmethod
    def active_taxes(cls):
        return TaxMaster.objects.using(cls.db_alias).filter(is_active=True)

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_product(product_id):
        try:
            return ProductMaster.objects.using(MASTERS_DB_ALIAS).get(pk=product_id)
        except ProductMaster.DoesNotExist as exc:
            raise MasterDataNotFound(f"Invalid product id '{product_id}'.") from exc

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_unit(unit_id):
        try:
            return UnitMaster.objects.using(MASTERS_DB_ALIAS).get(pk=unit_id)
        except UnitMaster.DoesNotExist as exc:
            raise MasterDataNotFound(f"Invalid unit id '{unit_id}'.") from exc

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_tax(tax_id):
        if not tax_id:
            return None
        try:
            return TaxMaster.objects.using(MASTERS_DB_ALIAS).get(pk=tax_id)
        except TaxMaster.DoesNotExist as exc:
            raise MasterDataNotFound(f"Invalid tax id '{tax_id}'.") from exc

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_tax_by_code(tax_code):
        if not tax_code:
            return None
        queryset = TaxMaster.objects.using(MASTERS_DB_ALIAS)
        tax = queryset.filter(name=tax_code).first()
        if tax is not None:
            return tax
        if str(tax_code).isdigit():
            return queryset.filter(pk=tax_code).first()
        return None

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_item(item_id):
        try:
            return (
                ItemMaster.objects.using(MASTERS_DB_ALIAS)
                .select_related("unit")
                .get(pk=item_id)
            )
        except ItemMaster.DoesNotExist as exc:
            raise MasterDataNotFound(f"Invalid item id '{item_id}'.") from exc

    @staticmethod
    @lru_cache(maxsize=256)
    def get_company_by_code(company_code):
        if not company_code:
            return None
        return CompanyMaster.objects.using(MASTERS_DB_ALIAS).filter(code=company_code).first()

    @staticmethod
    @lru_cache(maxsize=256)
    def get_project_by_code(project_code):
        if not project_code:
            return None
        return ProjectMaster.objects.using(MASTERS_DB_ALIAS).filter(code=project_code).first()

    @classmethod
    def sync_procurement_suppliers(cls):
        master_suppliers = (
            SupplierProfileMaster.objects.using(cls.db_alias)
            .filter(is_delete=False, is_active=True)
            .select_related("msme_type")
            .order_by("vendor_name")
        )

        for master_supplier in master_suppliers:
            name = master_supplier.vendor_name.strip()
            Supplier.objects.update_or_create(
                name=name,
                defaults={
                    "supplier_code": generated_supplier_code(master_supplier.id),
                    "gst_no": master_supplier.gst_no or "",
                    "pan_no": master_supplier.pan_no or "",
                    "msme_type": (
                        master_supplier.msme_type.name
                        if getattr(master_supplier, "msme_type", None)
                        else ""
                    ),
                    "contact_person": "",
                    "contact_no": master_supplier.phone_no or "",
                    "address": master_supplier.address or "",
                    "is_active": bool(master_supplier.is_active),
                },
            )


class UserLookupService:
    @staticmethod
    @lru_cache(maxsize=256)
    def get_user_type_name(username):
        if not username:
            return ""

        try:
            with connections[MASTERS_DB_ALIAS].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT ut.name
                    FROM admin_master_usercreation uc
                    LEFT JOIN admin_master_usertype ut ON uc.user_type_id = ut.id
                    WHERE LOWER(uc.username) = LOWER(%s)
                    LIMIT 1
                    """,
                    [username],
                )
                row = cursor.fetchone()
        except Exception:
            return ""

        return str(row[0]).strip().lower() if row and row[0] else ""
