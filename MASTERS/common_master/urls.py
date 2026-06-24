from django.urls import path, include

from MASTERS.api_router import ExtendedDefaultRouter
from collections import OrderedDict
from . import views
from django.conf import settings
from django.conf.urls.static import static
# Initialize router for ViewSets
router = ExtendedDefaultRouter()
router.register(r'continents-list', views.ContinentViewSet)
router.extra_api_root_dict = OrderedDict ({
    "countries": "country-list",
    "countries-create": "country-create",
    "continents": "continent-list",
    "continents-create": "continent-create",
    "states": "state-list",
    "states-create": "state-create",
    "cities": "city-list",
    "city-types": "city-types",
    "cities-create": "city-create",
    "taxes": "tax-list",
    "taxes-create": "tax-create",
    "companies": "company-list",
    "companies-create": "company-create",
    "projects": "project-list",
    "projects-create": "project-create",
    "countries-dropdown": "countries-dropdown",
    "customers": "customer-list",
"customers-create": "customer-create",
"contact-persons": "contact-person-list",
"contact-persons-create": "contact-person-create",
"account-details": "account-details-list",
"account-details-create": "account-details-create",
"billing-details": "billing-details-list",
"billing-details-create": "billing-details-create",
"shipping-details": "shipping-details-list",
"shipping-details-create": "shipping-details-create",
"documents": "document-list",
"documents-create": "document-create",
"suppliers": "supplier-list",
"suppliers-create": "supplier-create",
"supplier-statutory": "supplier-statutory-list",
"supplier-statutory-create": "supplier-statutory-create",
"supplier-accounts": "supplier-account-list",
"supplier-accounts-create": "supplier-account-create",
"supplier-billing": "supplier-billing-list",
"supplier-billing-create": "supplier-billing-create",
"supplier-shipping": "supplier-shipping-list",
"supplier-shipping-create": "supplier-shipping-create",
"supplier-documents": "supplier-document-list",
"supplier-documents-create": "supplier-document-create",
})


# Country endpoints
country_patterns = [
    path('countries/', views.country_list, name='country-list'),
    path('countries/create/', views.create_country, name='country-create'),
    path('countries/<int:pk>/', views.update_country, name='country-update'),
    path('countries/<int:pk>/toggle/', views.toggle_country, name='country-toggle'),
]

# Continent endpoints
continent_patterns = [
    path('continents/', views.continent_list, name='continent-list'),
    path('continents/create/', views.create_continent, name='continent-create'),
    path('continents/<int:pk>/', views.update_continent, name='continent-update'),
    path('continents/<int:pk>/toggle/', views.toggle_continent, name='continent-toggle'),
]

# State endpoints
state_patterns = [
    path('states/', views.list_states, name='state-list'),
    path('states/create/', views.create_state, name='state-create'),
    path('states/<int:pk>/', views.update_state, name='state-update'),
    path('states/toggle/<int:pk>/', views.toggle_state, name='state-toggle'),
]

# City endpoints
city_patterns = [
    path('cities/types/', views.get_city_types, name='city-types'),
    path('cities/list/', views.list_city, name='city-list'),
    path('cities/create/', views.create_city, name='city-create'),
    path('cities/toggle/<int:pk>/', views.toggle_city, name='city-toggle'),
    path('cities/<int:pk>/', views.city_detail, name='city-detail'),
]

# Tax endpoints
tax_patterns = [
    path('taxes/', views.list_tax, name='tax-list'),
    path('taxes/create/', views.create_tax, name='tax-create'),
    path('taxes/<int:pk>/', views.get_tax, name='tax-detail'),
    path('taxes/<int:pk>/toggle/', views.toggle_tax, name='tax-toggle'),
]

#Company Creation
company_patterns = [
    path('company/', views.list_company, name='company-list'),
    path('company/create/', views.create_company, name='company-create'),
    # path('company/<int:pk>/', views.update_company),
    path('company/<int:pk>/toggle/', views.toggle_company, name='company-toggle'),
]

# Project Creation
project_patterns = [
    path('projects/', views.list_project, name='project-list'),
    path('projects/create/', views.create_project, name='project-create'),
    # path('projects/<int:pk>/', views.update_project),
    path('projects/<int:pk>/toggle/', views.toggle_project, name='project-toggle'),
]

# Dropdown endpoints (placed at end for lower priority)
dropdown_patterns = [
    path('countries/dropdown/', views.get_countries, name='countries-dropdown'),
    path('states/by-country/<int:country_id>/', views.get_states_by_country, name='states-by-country'),
    path('projects/dropdown/', views.get_projects_dropdown, name='projects-dropdown'),
    path('projects/company-dropdown/', views.get_companies, name='projects-company-dropdown'),
    path('projects/application-types/', views.get_application_types, name='projects-application-types'),
    path('documents/types/', views.get_document_types, name='document-types'),
    path('suppliers/groups/', views.get_supplier_groups, name='supplier-groups'),
    path('suppliers/msme-types/', views.get_msme_types, name='supplier-msme-types'),
    path('suppliers/projects/', views.get_supplier_projects, name='supplier-projects'),
]
# Customer endpoints
customer_patterns = [
    path('customers/', views.list_customers, name='customer-list'),
    path('customers/create/', views.create_customer, name='customer-create'),
    path('customers/<int:pk>/', views.update_customer, name='customer-update'),
    path('customers/<int:pk>/toggle/', views.toggle_customer, name='customer-toggle'),
]
contact_person_patterns = [
    path('contact-persons/', views.list_contact_persons, name='contact-person-list'),
    path('contact-persons/create/', views.create_contact_person, name='contact-person-create'),
    path('contact-persons/<int:pk>/', views.update_contact_person, name='contact-person-update'),
    path('contact-persons/<int:pk>/toggle/', views.toggle_contact_person, name='contact-person-toggle'),
]
customer_statutory_patterns = [
    path('customer-statutory/', views.list_customer_statutory, name='customer-statutory-list'),
    path('customer-statutory/create/', views.create_customer_statutory, name='customer-statutory-create'),
    path('customer-statutory/<int:pk>/', views.update_customer_statutory, name='customer-statutory-update'),
    path('customer-statutory/<int:pk>/toggle/', views.toggle_customer_statutory, name='customer-statutory-toggle'),
]
account_details_patterns = [
    path('account-details/', views.list_account_details, name='account-details-list'),
    path('account-details/create/', views.create_account_details, name='account-details-create'),
    path('account-details/<int:pk>/', views.update_account_details, name='account-details-update'),
    path('account-details/<int:pk>/toggle/', views.toggle_account_details, name='account-details-toggle'),
]
billing_patterns = [
    path('billing-details/', views.list_billing_details, name='billing-details-list'),
    path('billing-details/create/', views.create_billing_details, name='billing-details-create'),
    path('billing-details/<int:pk>/', views.update_billing_details, name='billing-details-update'),
    path('billing-details/<int:pk>/toggle/', views.toggle_billing_details, name='billing-details-toggle'),
]
shipping_patterns = [
    path('shipping-details/', views.list_shipping_details, name='shipping-details-list'),
    path('shipping-details/create/', views.create_shipping_details, name='shipping-details-create'),
    path('shipping-details/<int:pk>/', views.update_shipping_details, name='shipping-details-update'),
    path('shipping-details/<int:pk>/toggle/', views.toggle_shipping_details, name='shipping-details-toggle'),
]
document_patterns = [
    path('documents/', views.list_documents, name='document-list'),
    path('documents/create/', views.create_document, name='document-create'),
    path('documents/<int:pk>/toggle/', views.toggle_document, name='document-toggle'),
]
supplier_patterns = [
    path('suppliers/', views.list_suppliers, name='supplier-list'),
    path('suppliers/create/', views.create_supplier, name='supplier-create'),
    path('suppliers/<int:pk>/', views.update_supplier, name='supplier-update'),
    path('suppliers/<int:pk>/toggle/', views.toggle_supplier, name='supplier-toggle'),
]
supplier_contact_patterns = [
    path('supplier-contact-persons/', views.list_supplier_contact_persons, name='supplier-contact-list'),
    path('supplier-contact-persons/create/', views.create_supplier_contact_person, name='supplier-contact-create'),
    path('supplier-contact-persons/<int:pk>/', views.update_supplier_contact_person, name='supplier-contact-update'),
    path('supplier-contact-persons/<int:pk>/toggle/', views.toggle_supplier_contact_person, name='supplier-contact-toggle'),
]
supplier_statutory_patterns = [
    path('supplier-statutory/', views.list_supplier_statutory, name='supplier-statutory-list'),
    path('supplier-statutory/create/', views.create_supplier_statutory, name='supplier-statutory-create'),
    path('supplier-statutory/<int:pk>/', views.update_supplier_statutory, name='supplier-statutory-update'),
    path('supplier-statutory/<int:pk>/toggle/', views.toggle_supplier_statutory, name='supplier-statutory-toggle'),

]
supplier_account_patterns = [
    path('supplier-accounts/', views.list_supplier_accounts, name='supplier-account-list'),
    path('supplier-accounts/create/', views.create_supplier_account, name='supplier-account-create'),
    path('supplier-accounts/<int:pk>/', views.update_supplier_account, name='supplier-account-update'),
    path('supplier-accounts/<int:pk>/toggle/', views.toggle_supplier_account, name='supplier-account-toggle'),
]
supplier_billing_patterns = [
    path('supplier-billing/', views.list_supplier_billing, name='supplier-billing-list'),
    path('supplier-billing/create/', views.create_supplier_billing, name='supplier-billing-create'),
    path('supplier-billing/<int:pk>/', views.update_supplier_billing, name='supplier-billing-update'),
    path('supplier-billing/<int:pk>/toggle/', views.toggle_supplier_billing, name='supplier-billing-toggle'),
]
supplier_shipping_patterns = [
    path('supplier-shipping/', views.list_supplier_shipping, name='supplier-shipping-list'),
    path('supplier-shipping/create/', views.create_supplier_shipping, name='supplier-shipping-create'),
    path('supplier-shipping/<int:pk>/', views.update_supplier_shipping, name='supplier-shipping-update'),
    path('supplier-shipping/<int:pk>/toggle/', views.toggle_supplier_shipping, name='supplier-shipping-toggle'),
]
supplier_document_patterns = [
    path('supplier-documents/', views.list_supplier_documents, name='supplier-document-list'),
    path('supplier-documents/create/', views.create_supplier_document, name='supplier-document-create'),
    path('supplier-documents/<int:pk>/toggle/', views.toggle_supplier_document, name='supplier-document-toggle'),
]
# Combine all patterns
urlpatterns = [
    path('', include(router.urls)),
] + country_patterns + continent_patterns + state_patterns + city_patterns + tax_patterns + dropdown_patterns + company_patterns + project_patterns + customer_patterns + contact_person_patterns + customer_statutory_patterns + account_details_patterns + billing_patterns + shipping_patterns + document_patterns+ supplier_patterns + supplier_contact_patterns + supplier_statutory_patterns+ supplier_account_patterns+ supplier_billing_patterns + supplier_shipping_patterns + supplier_document_patterns
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
