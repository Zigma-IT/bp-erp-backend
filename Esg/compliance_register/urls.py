from django.urls import path

from .views import (
    # Compliance TYPE
    ESGComplianceRegisterListCreateAPIView,
    ESGComplianceRegisterRetrieveAPIView,
    ESGComplianceRegisterUpdateAPIView,
    ESGComplianceRegisterDeleteAPIView,
    ESGComplianceCreateAPIView,
    ESGComplianceListAPIView,
    ESGComplianceRetrieveAPIView,
    ESGComplianceUpdateAPIView,
    ESGComplianceDeleteAPIView,
    # Compliance ENTRY

    ESGComplianceEntryListAPIView,
    ESGComplianceEntryCreateAPIView,
    ESGComplianceEntryBulkCreateAPIView,
    ESGComplianceEntryRetrieveAPIView,
    ESGComplianceEntryUpdateAPIView,
    ESGComplianceEntryDeleteAPIView,

    # Insurance Register
    InsuranceRegisterCreateAPIView,
    InsuranceRegisterListAPIView,
    InsuranceRegisterRetrieveAPIView,
    InsuranceRegisterUpdateAPIView,
    InsuranceRegisterDeleteAPIView,

    ESGComplianceHistoryListAPIView,
    ESGComplianceHistoryRetrieveAPIView,
    ESGComplianceRenewAPIView,
)

urlpatterns = [

    # ── Compliance TYPE (generic) ────────────────────────────────────
    path("esg-compliance-register/",
         ESGComplianceRegisterListCreateAPIView.as_view(),
         name="esg-register-list-create"),
    path("esg-compliance-register/<int:pk>/",
         ESGComplianceRegisterRetrieveAPIView.as_view(),
         name="esg-register-detail"),
    path("esg-compliance-register/update/<int:pk>/",
         ESGComplianceRegisterUpdateAPIView.as_view(),
         name="esg-register-update"),
    path("esg-compliance-register/delete/<int:pk>/",
         ESGComplianceRegisterDeleteAPIView.as_view(),
         name="esg-register-delete"),

    # ── Compliance TYPE (APIView) ────────────────────────────────────
    path("esg-compliance/create/",
         ESGComplianceCreateAPIView.as_view(),
         name="esg-compliance-create"),
    path("esg-compliance/list/",
         ESGComplianceListAPIView.as_view(),
         name="esg-compliance-list"),
    path("esg-compliance/<int:id>/",
         ESGComplianceRetrieveAPIView.as_view(),
         name="esg-compliance-detail"),
    path("esg-compliance/update/<int:id>/",
         ESGComplianceUpdateAPIView.as_view(),
         name="esg-compliance-update"),
    path("esg-compliance/delete/<int:id>/",
         ESGComplianceDeleteAPIView.as_view(),
         name="esg-compliance-delete"),

    # ── Compliance ENTRY ─────────────────────────────────────────────
    path("esg-compliance-entry/",
         ESGComplianceEntryListAPIView.as_view(),
         name="esg-entry-list"),
    path("esg-compliance-entry/create/",
         ESGComplianceEntryCreateAPIView.as_view(),
         name="esg-entry-create"),
    path("esg-compliance-entry/bulk-create/",
         ESGComplianceEntryBulkCreateAPIView.as_view(),
         name="esg-entry-bulk-create"),
    path("esg-compliance-entry/<int:id>/",
         ESGComplianceEntryRetrieveAPIView.as_view(),
         name="esg-entry-detail"),
    path("esg-compliance-entry/update/<int:id>/",
         ESGComplianceEntryUpdateAPIView.as_view(),
         name="esg-entry-update"),
    path("esg-compliance-entry/delete/<int:id>/",
         ESGComplianceEntryDeleteAPIView.as_view(),
         name="esg-entry-delete"),


    path(
        "insurance-register/create/",
        InsuranceRegisterCreateAPIView.as_view(),
        name="insurance-register-create"
    ),

    path(
        "insurance-register/list/",
        InsuranceRegisterListAPIView.as_view(),
        name="insurance-register-list"
    ),

    path(
        "insurance-register/<int:id>/",
        InsuranceRegisterRetrieveAPIView.as_view(),
        name="insurance-register-detail"
    ),

    path(
        "insurance-register/update/<int:id>/",
        InsuranceRegisterUpdateAPIView.as_view(),
        name="insurance-register-update"
    ),

    path(
        "insurance-register/delete/<int:id>/",
        InsuranceRegisterDeleteAPIView.as_view(),
        name="insurance-register-delete"
    ),

    # ── Compliance History ─────────────────────────────

path(
    "esg-compliance-history/<int:id>/",
    ESGComplianceHistoryRetrieveAPIView.as_view(),
    name="esg-history-detail"
),

path(
    "esg-compliance-history/list/<int:entry_id>/",
    ESGComplianceHistoryListAPIView.as_view(),
    name="esg-history-list"
),

# Renewal API

path(
    "esg-compliance-entry/renew/<int:id>/",
    ESGComplianceRenewAPIView.as_view(),
    name="esg-entry-renew"
),
]

