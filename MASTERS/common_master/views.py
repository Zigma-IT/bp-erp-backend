"""Common master APIs for geography, tax, company, and project lookups."""

from contextlib import closing

from django.db import connections
from django.db.models import Q
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from MASTERS.schema_utils import DATATABLE_PARAMETERS
from .models import City, CommonMaster, Continent, Country, State, Tax, Company, Project, CustomerProfile , CustomerContactPerson , CustomerStatutoryDetails , CustomerAccountDetails , CustomerBillingDetails , CustomerShippingDetails , CustomerDocument , SupplierProfile , SupplierContactPerson , SupplierStatutoryDetails , SupplierAccountDetails , SupplierBillingDetails , SupplierShippingDetails , SupplierDocuments
from .serializers import (
    CitySerializer,
    ContinentSerializer,
    CountrySerializer,
    StateSerializer,
    TaxSerializer,
    CompanySerializer,
    ProjectSerializer,
    CustomerProfileSerializer,
    CustomerContactPersonSerializer,
    CustomerStatutoryDetailsSerializer,
    CustomerAccountDetailsSerializer,
    CustomerBillingDetailsSerializer,
    CustomerShippingDetailsSerializer,
    CustomerDocumentSerializer,
    SupplierProfileSerializer,
    SupplierContactPersonSerializer,
    SupplierStatutoryDetailsSerializer, 
    SupplierAccountDetailsSerializer,
    SupplierBillingDetailsSerializer,
    SupplierShippingDetailsSerializer, 
    SupplierDocumentsSerializer, 
)


def _masters_db_alias() -> str:
    return "masters_db" if "masters_db" in connections.databases else "default"


def _fetch_all_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class ContinentViewSet(viewsets.ModelViewSet):
    queryset = Continent.objects.filter(status=True).order_by("name")
    serializer_class = ContinentSerializer


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.select_related("continent").all().order_by("id")
    serializer_class = CountrySerializer

    def list(self, request, *args, **kwargs):
        search = request.GET.get("search[value]", "")
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))

        queryset = self.queryset
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(code__icontains=search)
                | Q(continent__name__icontains=search)
            )

        total = self.queryset.count()
        filtered = queryset.count()
        queryset = queryset[start : start + length]

        data = []
        for index, obj in enumerate(queryset, start=1):
            data.append(
                {
                    "id": obj.pk,
                    "sno": start + index,
                    "country_name": obj.name,
                    "continent_name": obj.continent.name,
                    "country_code": obj.code,
                    "currency": obj.currency or "-",
                    "status": obj.status,
                }
            )

        return Response(
            {
                "draw": int(request.GET.get("draw", 1)),
                "recordsTotal": total,
                "recordsFiltered": filtered,
                "data": data,
            }
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = request.data.get("status", instance.status)
        instance.save(update_fields=["status"])
        return Response({"message": "Status updated"})


@api_view(["GET"])
def country_list(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search = request.GET.get("search[value]", "")

    queryset = Country.objects.select_related("continent").all()
    total = queryset.count()

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
            | Q(continent__name__icontains=search)
        )

    filtered = queryset.count()
    serializer = CountrySerializer(queryset[start : start + length], many=True)

    data = []
    for index, item in enumerate(serializer.data, start=1):
        data.append(
            {
                "sno": start + index,
                "country_name": item["name"],
                "country_code": item["code"],
                "continent": item.get("continent_name") or item["continent"],
                "continent_id": item["continent"],
                "currency": item["currency"] or "-",
                "status": "Active" if item["status"] else "Inactive",
                "id": item["id"],
            }
        )

    return Response(
        {
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": data,
        }
    )

@api_view(["POST"])
def create_country(request):
    serializer = CountrySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def update_country(request, pk):
    try:
        obj = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = CountrySerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated successfully", "data": serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def toggle_country(request, pk):
    try:
        obj = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    obj.status = not obj.status
    obj.save(update_fields=["status"])
    return Response({"message": "Status toggled", "status": obj.status})


@api_view(["GET"])
def continent_list(request):
    queryset = Continent.objects.filter(status=True).order_by("name")
    serializer = ContinentSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def create_continent(request):
    serializer = ContinentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def update_continent(request, pk):
    try:
        obj = Continent.objects.get(pk=pk)
    except Continent.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ContinentSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated successfully", "data": serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def toggle_continent(request, pk):
    try:
        obj = Continent.objects.get(pk=pk)
    except Continent.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    obj.status = not obj.status
    obj.save(update_fields=["status"])
    return Response({"message": "Status toggled", "status": obj.status})


@api_view(["GET"])
def get_countries(request):
    countries = Country.objects.filter(status=True).order_by("name")
    serializer = CountrySerializer(countries, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def create_state(request):
    serializer = StateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "State created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def list_states(request):
    states = State.objects.select_related("country").all().order_by("id")

    data = []
    for index, state_obj in enumerate(states, start=1):
        data.append(
            {
                "id": state_obj.pk,
                "sno": index,
                "country": state_obj.country.name,
                "country_id": state_obj.country_id,
                "state_name": state_obj.name,
                "is_active": state_obj.is_active,
            }
        )

    return Response({"data": data})


@api_view(["PUT"])
def update_state(request, pk):
    try:
        state_obj = State.objects.get(pk=pk)
    except State.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = StateSerializer(state_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "State updated successfully", "data": serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def toggle_state(request, pk):
    try:
        state_obj = State.objects.get(id=pk)
    except State.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    state_obj.is_active = not state_obj.is_active
    state_obj.save(update_fields=["is_active"])
    return Response({"message": "Status updated"})


@api_view(["GET"])
def get_city_types(request):
    data = CommonMaster.objects.filter(type="CITY_TYPE", is_active=True).values("id", "name")
    return Response(list(data))


@api_view(["GET"])
def get_states_by_country(request, country_id):
    states = State.objects.filter(country_id=country_id, is_active=True).values("id", "name")
    return Response(list(states))


@api_view(["POST"])
def create_city(request):
    serializer = CitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True, "message": "City created"}, status=status.HTTP_201_CREATED)
    return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
def list_city(request):
    search = request.GET.get("search[value]", "")
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    draw = int(request.GET.get("draw", 1))

    base_queryset = City.objects.select_related("country", "state", "city_type")
    queryset = base_queryset

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(pincode__icontains=search)
            | Q(state__name__icontains=search)
            | Q(country__name__icontains=search)
        )

    total = base_queryset.count()
    filtered = queryset.count()
    cities = queryset[start : start + length]

    data = []
    for index, city in enumerate(cities, start=1):
        data.append(
            {
                "sno": start + index,
                "city": city.name,
                "state": city.state.name,
                "state_id": city.state_id,
                "country": city.country.name,
                "country_id": city.country_id,
                "pincode": city.pincode,
                "city_type_id": city.city_type_id,
                "status": city.is_active,
                "id": city.pk,
            }
        )

    return Response(
        {
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": data,
        }
    )


@api_view(["POST"])
def toggle_city(request, pk):
    try:
        city = City.objects.get(id=pk)
    except City.DoesNotExist:
        return Response(
            {"status": False, "message": "City not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    city.is_active = not city.is_active
    city.save(update_fields=["is_active"])
    return Response({"status": True})


@api_view(["GET", "PUT"])
def city_detail(request, pk):
    try:
        city = City.objects.get(id=pk)
    except City.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = CitySerializer(city)
        return Response(serializer.data)

    serializer = CitySerializer(city, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True, "message": "City updated", "data": serializer.data})
    return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def create_tax(request):
    serializer = TaxSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True, "message": "Tax created"}, status=status.HTTP_201_CREATED)
    return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def list_tax(request):
    search = request.GET.get("search[value]", "")
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    draw = int(request.GET.get("draw", 1))

    base_queryset = Tax.objects.select_related("country")
    queryset = base_queryset

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(country__name__icontains=search)
            | Q(value__icontains=search)
        )

    total = base_queryset.count()
    filtered = queryset.count()
    taxes = queryset[start : start + length]

    data = []
    for index, tax in enumerate(taxes, start=1):
        data.append(
            {
                "sno": start + index,
                "tax_name": tax.name,
                "tax_value": float(tax.value),
                "country": tax.country.name if tax.country else "-",
                "status": tax.is_active,
                "id": tax.pk,
            }
        )

    return Response(
        {
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": data,
        }
    )


@api_view(["POST"])
def toggle_tax(request, pk):
    try:
        tax = Tax.objects.get(id=pk)
    except Tax.DoesNotExist:
        return Response({"status": False, "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    tax.is_active = not tax.is_active
    tax.save(update_fields=["is_active"])
    return Response({"status": True})


@api_view(["GET", "PUT", "PATCH"])
def get_tax(request, pk):
    try:
        tax = Tax.objects.get(id=pk)
    except Tax.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = TaxSerializer(tax)
        return Response(serializer.data)

    serializer = TaxSerializer(
        tax,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"status": True, "message": "Tax updated", "data": serializer.data}
        )
    return Response(
        {"status": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


# Company Creation
@api_view(["GET"])
def list_company(request):
    search = request.GET.get("search[value]", "")
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    draw = int(request.GET.get("draw", 1))

    base_queryset = Company.objects.select_related("country", "state", "city")
    queryset = base_queryset

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(city__name__icontains=search)
        )

    total = base_queryset.count()
    filtered = queryset.count()

    companies = queryset[start:start+length]

    data = []
    for i, obj in enumerate(companies, start=1):
        data.append({
            "sno": start + i,
            "company_name": obj.name,
            "company_code": obj.code,
            "state": obj.state.name if obj.state else "",
            "city": obj.city.name if obj.city else "",
            "pincode": obj.pincode,
            "latitude": obj.latitude,
            "longitude": obj.longitude,
            "logo": obj.logo.url if obj.logo else "",
            "document": obj.document.url if obj.document else "",
            "status": "Active" if obj.is_active else "Inactive",
            "id": obj.pk
        })

    return Response({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })

@api_view(["POST"])
def create_company(request):
    serializer = CompanySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True, "message": "Created"}, status=status.HTTP_201_CREATED)
    return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def toggle_company(request, pk):
    obj = Company.objects.get(pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active"])
    return Response({"status": True})

# Project Creation
@api_view(["GET"])
def list_project(request):
    search = request.GET.get("search[value]", "")
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    draw = int(request.GET.get("draw", 1))

    base_queryset = Project.objects.select_related(
        "company", "state", "city", "application_type"
    )

    queryset = base_queryset

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(company__name__icontains=search)
        )

    total = base_queryset.count()
    filtered = queryset.count()

    projects = queryset[start:start+length]

    data = []
    for i, obj in enumerate(projects, start=1):
        data.append({
            "sno": start + i,
            "company_name": obj.company.name,
            "project_name": obj.name,
            "project_code": obj.code,
            "client_name": obj.client_name,
            "application_type": obj.application_type.name if obj.application_type else "",
            "capacity": obj.capacity,
            "state": obj.state.name if obj.state else "",
            "city": obj.city.name if obj.city else "",
            "contact_person": obj.contact_person,
            "contact_number": obj.contact_number,
            "status": "Active" if obj.is_active else "Inactive",
            "id": obj.pk
        })

    return Response({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })

@api_view(["POST"])
def create_project(request):
    serializer = ProjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True, "message": "Project created"}, status=status.HTTP_201_CREATED)
    return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["PATCH"])
def toggle_project(request, pk):
    obj = Project.objects.get(pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active"])
    return Response({"status": True})

@api_view(["GET"])
def get_companies(request):
    data = Company.objects.filter(is_active=True).values("id", "name")
    return Response(list(data))


@api_view(["GET"])
def get_application_types(request):
    queryset = CommonMaster.objects.filter(
        Q(type="APPLICATION_TYPE")
        | Q(type="Application Type")
        | Q(type="APPLICATION TYPE"),
        is_active=True,
    )

    if settings.DEBUG and not queryset.exists():
        try:
            from .bootstrap import ensure_dev_common_master_data

            ensure_dev_common_master_data()
            queryset = CommonMaster.objects.filter(
                Q(type="APPLICATION_TYPE")
                | Q(type="Application Type")
                | Q(type="APPLICATION TYPE"),
                is_active=True,
            )
        except Exception:
            pass

    data = queryset.values("id", "name")
    return Response(list(data))


@api_view(["GET"])
def get_document_types(request):
    queryset = CommonMaster.objects.filter(type="DOCUMENT_TYPE", is_active=True)

    if settings.DEBUG and not queryset.exists():
        try:
            from .bootstrap import ensure_dev_common_master_data

            ensure_dev_common_master_data()
            queryset = CommonMaster.objects.filter(type="DOCUMENT_TYPE", is_active=True)
        except Exception:
            pass

    return Response(list(queryset.values("id", "name")))


@api_view(["GET"])
def get_supplier_groups(request):
    queryset = CommonMaster.objects.filter(
        Q(type="SUPPLIER_GROUP") | Q(type="GROUP"),
        is_active=True,
    )

    if settings.DEBUG and not queryset.exists():
        try:
            from .bootstrap import ensure_dev_common_master_data

            ensure_dev_common_master_data()
            queryset = CommonMaster.objects.filter(
                Q(type="SUPPLIER_GROUP") | Q(type="GROUP"),
                is_active=True,
            )
        except Exception:
            pass

    return Response(list(queryset.values("id", "name")))


@api_view(["GET"])
def get_msme_types(request):
    queryset = CommonMaster.objects.filter(type="MSME_TYPE", is_active=True)

    if settings.DEBUG and not queryset.exists():
        try:
            from .bootstrap import ensure_dev_common_master_data

            ensure_dev_common_master_data()
            queryset = CommonMaster.objects.filter(type="MSME_TYPE", is_active=True)
        except Exception:
            pass

    return Response(list(queryset.values("id", "name")))


@api_view(["GET"])
def get_supplier_projects(request):
    queryset = Project.objects.filter(is_active=True).values("id", "name")
    return Response(list(queryset))


country_list = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(country_list)
create_country = extend_schema(
    request=CountrySerializer,
    responses=OpenApiTypes.OBJECT,
)(create_country)
update_country = extend_schema(
    request=CountrySerializer,
    responses=OpenApiTypes.OBJECT,
)(update_country)
toggle_country = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_country)

continent_list = extend_schema(
    responses=ContinentSerializer(many=True),
)(continent_list)
create_continent = extend_schema(
    request=ContinentSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_continent)
update_continent = extend_schema(
    request=ContinentSerializer,
    responses=OpenApiTypes.OBJECT,
)(update_continent)
toggle_continent = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_continent)
get_countries = extend_schema(
    responses=CountrySerializer(many=True),
)(get_countries)

create_state = extend_schema(
    request=StateSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_state)
list_states = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(list_states)
toggle_state = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_state)

get_city_types = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(get_city_types)
get_states_by_country = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(get_states_by_country)
create_city = extend_schema(
    request=CitySerializer,
    responses=OpenApiTypes.OBJECT,
)(create_city)
list_city = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(list_city)
toggle_city = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_city)
get_city = extend_schema(
    responses=CitySerializer,
)(city_detail)

create_tax = extend_schema(
    request=TaxSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_tax)
list_tax = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    operation_id="api_masters_taxes_list",
    responses=OpenApiTypes.OBJECT,
)(list_tax)
toggle_tax = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_tax)
get_tax = extend_schema(
    operation_id="api_masters_taxes_detail",
    responses=TaxSerializer,
)(get_tax)

list_company = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(list_company)
create_company = extend_schema(
    request=CompanySerializer,
    responses=OpenApiTypes.OBJECT,
)(create_company)
toggle_company = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_company)

list_project = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(list_project)
create_project = extend_schema(
    request=ProjectSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_project)
toggle_project = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_project)
get_companies = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(get_companies)
get_application_types = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(get_application_types)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>Customer Creation <<<<<<<<<<>>>><<<<<<<<<<<<<<<
# LIST
@api_view(['GET'])
def list_customers(request):
    customers = CustomerProfile.objects.filter(is_delete=False)
    search = request.GET.get("search", "").strip()
    if search:
        customers = customers.filter(
            Q(customer_name__icontains=search)
            | Q(customer_no__icontains=search)
            | Q(gst_no__icontains=search)
            | Q(email_id__icontains=search)
        )

    data = []
    for index, customer in enumerate(customers, start=1):
        data.append({
            "id": customer.pk,
            "sno": index,
            "customer_name": customer.customer_name,
            "customer_no": customer.customer_no,
            "customer_group_id": customer.customer_group_id,
            "customer_sub_category_id": customer.customer_sub_category_id,
            "property": "",
            "currency": customer.currency,
            "gst_no": customer.gst_no,
            "created_by": customer.sess_user_type or "",
            "status": customer.is_active,
        })
    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_customer(request):
    if request.method == 'GET':
        serializer = CustomerProfileSerializer()
        return Response(serializer.data)
    serializer = CustomerProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Customer created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# UPDATE
@api_view(['GET', 'PUT', 'PATCH'])
def update_customer(request, pk):
    try:
        customer = CustomerProfile.objects.get(pk=pk)
    except CustomerProfile.DoesNotExist:
        return Response({"error": "Customer not found"}, status=404)

    if request.method == 'GET':
        serializer = CustomerProfileSerializer(customer)
        return Response(serializer.data)

    serializer = CustomerProfileSerializer(customer, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Customer updated successfully",
            "data": serializer.data
        })
    return Response(serializer.errors, status=400)


# DELETE (soft delete)
@api_view(['DELETE'])
def toggle_customer(request, pk):
    try:
        customer = CustomerProfile.objects.get(pk=pk)
    except CustomerProfile.DoesNotExist:
        return Response({"error": "Customer not found"}, status=404)

    customer.is_delete = True
    customer.save()

    return Response({"message": "Customer deleted successfully"})


# LIST
@api_view(['GET'])
def list_contact_persons(request):
    customer_id = request.GET.get("customer_id")
    params = []
    where_clause = "WHERE cp.is_delete = 0"
    if customer_id:
        where_clause += " AND c.id = %s"
        params.append(customer_id)

    query = f"""
        SELECT
            cp.contact_person_id AS id,
            c.id AS customer_id,
            c.customer_name AS customer_name,
            cp.contact_person_name AS name,
            cp.contact_person_designation AS designation,
            cp.contact_person_email AS email,
            cp.contact_person_contact_no AS contact_no,
            cp.is_active AS status
        FROM customer_contact_person cp
        LEFT JOIN customer_profile c
            ON c.unique_id = cp.customer_profile_unique_id
        {where_clause}
        ORDER BY cp.contact_person_id DESC
    """

    with closing(connections[_masters_db_alias()].cursor()) as cursor:
        cursor.execute(query, params)
        rows = _fetch_all_dicts(cursor)

    data = []
    for index, row in enumerate(rows, start=1):
        data.append({
            "sno": index,
            "id": row["id"],
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"] or "",
            "name": row["name"] or "",
            "designation": row["designation"] or "",
            "email": row["email"] or "",
            "contact_no": row["contact_no"] or "",
            "status": bool(row["status"]),
        })

    return Response({"data": data})


@api_view(['GET'])
def list_customer_statutory(request):
    customer_id = request.GET.get("customer_id")
    params = []
    where_clause = "WHERE 1 = 1"
    if customer_id:
        where_clause += " AND c.id = %s"
        params.append(customer_id)

    query = f"""
        SELECT
            s.id AS id,
            c.id AS customer,
            c.customer_name AS customer_name,
            s.ecc_no AS ecc_no,
            s.commissionerate AS commissionerate,
            s.division AS division,
            s.stat_range AS `range`,
            s.cst_no AS cst_no,
            s.tin_no AS trn_no,
            s.service_tax_no AS service_tax_no,
            s.iec_code AS iec_code,
            s.cin_no AS cin_no,
            s.tan_no AS tan_no
        FROM cust_statutory_details s
        LEFT JOIN customer_profile c
            ON c.unique_id = s.customer_profile_unique_id
        {where_clause}
        ORDER BY s.id DESC
    """

    with closing(connections[_masters_db_alias()].cursor()) as cursor:
        cursor.execute(query, params)
        rows = _fetch_all_dicts(cursor)

    data = []
    for row in rows:
        data.append({
            "id": row["id"],
            "customer": row["customer"],
            "customer_name": row["customer_name"] or "",
            "ecc_no": row["ecc_no"] or "",
            "commissionerate": row["commissionerate"] or "",
            "division": row["division"] or "",
            "range": row["range"] or "",
            "cst_no": row["cst_no"] or "",
            "trn_no": row["trn_no"] or "",
            "service_tax_no": row["service_tax_no"] or "",
            "iec_code": row["iec_code"] or "",
            "cin_no": row["cin_no"] or "",
            "tan_no": row["tan_no"] or "",
            "status": True,
        })

    return Response({"data": data})


@api_view(['GET', 'POST'])
def create_customer_statutory(request):
    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["customer"]
        })

    serializer = CustomerStatutoryDetailsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        serializer.save()
    except Exception as exc:
        return Response(
            {"error": f"Unable to create customer statutory details: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        "message": "Statutory details created successfully",
        "data": serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
def update_customer_statutory(request, pk):
    try:
        obj = CustomerStatutoryDetails.objects.get(pk=pk)
    except CustomerStatutoryDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = CustomerStatutoryDetailsSerializer(obj, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    try:
        serializer.save()
    except Exception as exc:
        return Response(
            {"error": f"Unable to update customer statutory details: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        "message": "Updated successfully",
        "data": serializer.data
    })


@api_view(['DELETE'])
def toggle_customer_statutory(request, pk):
    try:
        obj = CustomerStatutoryDetails.objects.get(pk=pk)
    except CustomerStatutoryDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# CREATE + GET (structure)
@api_view(['GET', 'POST'])
def create_contact_person(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": [
                "customer",
                "contact_person_name",
                "contact_person_contact_no"
            ]
        })

    serializer = CustomerContactPersonSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Contact person created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_contact_person(request, pk):
    try:
        obj = CustomerContactPerson.objects.get(pk=pk)
    except CustomerContactPerson.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = CustomerContactPersonSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE (soft delete)
@api_view(['DELETE'])
def toggle_contact_person(request, pk):
    try:
        obj = CustomerContactPerson.objects.get(pk=pk)
    except CustomerContactPerson.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# LIST
@api_view(['GET'])
def list_account_details(request):
    customer_id = request.GET.get("customer_id")
    params = []
    where_clause = "WHERE a.is_delete = 0"
    if customer_id:
        where_clause += " AND c.id = %s"
        params.append(customer_id)

    query = f"""
        SELECT
            a.account_details_id AS id,
            c.id AS customer_id,
            c.customer_name AS customer_name,
            a.bank_name AS bank_name,
            a.bank_address AS bank_address,
            a.account_no AS account_no,
            a.ifsc_code AS ifsc_code,
            a.beneficiary_account_name AS beneficiary_name,
            a.beneficiary_account_name AS beneficiary_account_name,
            a.is_active AS status
        FROM customer_account_details a
        LEFT JOIN customer_profile c
            ON c.unique_id = a.customer_profile_unique_id
        {where_clause}
        ORDER BY a.account_details_id DESC
    """

    with closing(connections[_masters_db_alias()].cursor()) as cursor:
        cursor.execute(query, params)
        rows = _fetch_all_dicts(cursor)

    data = []
    for index, row in enumerate(rows, start=1):
        data.append({
            "sno": index,
            "id": row["id"],
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"] or "",
            "bank_name": row["bank_name"] or "",
            "bank_address": row["bank_address"] or "",
            "account_no": row["account_no"] or "",
            "ifsc_code": row["ifsc_code"] or "",
            "beneficiary_name": row["beneficiary_name"] or "",
            "beneficiary_account_name": row["beneficiary_account_name"] or "",
            "status": bool(row["status"]),
        })

    return Response({"data": data})


# CREATE + GET STRUCTURE
@api_view(['GET', 'POST'])
def create_account_details(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": [
                "customer",
                "bank_name",
                "account_no",
                "ifsc_code"
            ]
        })

    serializer = CustomerAccountDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Account details created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_account_details(request, pk):
    try:
        obj = CustomerAccountDetails.objects.get(pk=pk)
    except CustomerAccountDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = CustomerAccountDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE (soft delete)
@api_view(['DELETE'])
def toggle_account_details(request, pk):
    try:
        obj = CustomerAccountDetails.objects.get(pk=pk)
    except CustomerAccountDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# LIST
@api_view(['GET'])
def list_billing_details(request):
    customer_id = request.GET.get("customer_id")
    params = []
    where_clause = "WHERE b.is_delete = 0"
    if customer_id:
        where_clause += " AND c.id = %s"
        params.append(customer_id)

    query = f"""
        SELECT
            b.billing_details_id AS id,
            c.id AS customer,
            b.name AS name,
            b.billing_address AS address,
            country_ref.id AS country,
            b.country AS country_name,
            state_ref.id AS state,
            b.state AS state_name,
            city_ref.id AS city,
            b.city AS city_name,
            b.contact_name AS contact_name,
            b.contact_no AS contact_no,
            b.billing_gst_no AS gst_no,
            b.gst_status AS gst_status,
            b.ecc_no AS ecc_no,
            b.is_active AS status
        FROM cust_billing_details b
        LEFT JOIN customer_profile c
            ON c.unique_id = b.customer_profile_unique_id
        LEFT JOIN common_master_country country_ref
            ON LOWER(TRIM(country_ref.name)) = LOWER(TRIM(b.country))
        LEFT JOIN common_master_state state_ref
            ON LOWER(TRIM(state_ref.name)) = LOWER(TRIM(b.state))
        LEFT JOIN common_master_city city_ref
            ON LOWER(TRIM(city_ref.name)) = LOWER(TRIM(b.city))
        {where_clause}
        ORDER BY b.billing_details_id DESC
    """

    with closing(connections[_masters_db_alias()].cursor()) as cursor:
        cursor.execute(query, params)
        rows = _fetch_all_dicts(cursor)

    data = []
    for index, row in enumerate(rows, start=1):
        data.append({
            "sno": index,
            "id": row["id"],
            "customer": row["customer"],
            "name": row["name"] or "",
            "address": row["address"] or "",
            "country": row["country"],
            "country_name": row["country_name"] or "",
            "state": row["state"],
            "state_name": row["state_name"] or "",
            "city": row["city"],
            "city_name": row["city_name"] or "",
            "contact_name": row["contact_name"] or "",
            "contact_no": row["contact_no"] or "",
            "gst_no": row["gst_no"] or "",
            "gst_status": row["gst_status"] or "",
            "ecc_no": row["ecc_no"] or "",
            "status": bool(row["status"]),
        })

    return Response({"data": data})


# CREATE + GET STRUCTURE
@api_view(['GET', 'POST'])
def create_billing_details(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": [
                "customer",
                "name",
                "address",
                "country",
                "state",
                "city"
            ]
        })

    serializer = CustomerBillingDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Billing created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_billing_details(request, pk):
    try:
        obj = CustomerBillingDetails.objects.get(pk=pk)
    except CustomerBillingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = CustomerBillingDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_billing_details(request, pk):
    try:
        obj = CustomerBillingDetails.objects.get(pk=pk)
    except CustomerBillingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})
    # LIST
@api_view(['GET'])
def list_shipping_details(request):
    customer_id = request.GET.get("customer_id")
    params = []
    where_clause = "WHERE s.is_delete = 0"
    if customer_id:
        where_clause += " AND c.id = %s"
        params.append(customer_id)

    query = f"""
        SELECT
            s.shipping_details_id AS id,
            c.id AS customer_id,
            s.name AS name,
            s.shipping_address AS address,
            country_ref.id AS country,
            s.country AS country_name,
            state_ref.id AS state,
            s.state AS state_name,
            city_ref.id AS city,
            s.city AS city_name,
            s.contact_name AS contact_name,
            s.contact_no AS contact_no,
            s.shipping_gst_no AS gst_no,
            s.gst_status AS gst_status,
            s.ecc_no AS ecc_no,
            0 AS same_as_billing
        FROM customer_shipping_details s
        LEFT JOIN customer_profile c
            ON c.unique_id = s.customer_profile_unique_id
        LEFT JOIN common_master_country country_ref
            ON LOWER(TRIM(country_ref.name)) = LOWER(TRIM(s.country))
        LEFT JOIN common_master_state state_ref
            ON LOWER(TRIM(state_ref.name)) = LOWER(TRIM(s.state))
        LEFT JOIN common_master_city city_ref
            ON LOWER(TRIM(city_ref.name)) = LOWER(TRIM(s.city))
        {where_clause}
        ORDER BY s.shipping_details_id DESC
    """

    with closing(connections[_masters_db_alias()].cursor()) as cursor:
        cursor.execute(query, params)
        rows = _fetch_all_dicts(cursor)

    data = []
    for row in rows:
        data.append({
            "id": row["id"],
            "customer_id": row["customer_id"],
            "name": row["name"] or "",
            "address": row["address"] or "",
            "country": row["country"],
            "country_name": row["country_name"] or "",
            "state": row["state"],
            "state_name": row["state_name"] or "",
            "city": row["city"],
            "city_name": row["city_name"] or "",
            "contact_name": row["contact_name"] or "",
            "contact_no": row["contact_no"] or "",
            "gst_no": row["gst_no"] or "",
            "gst_status": row["gst_status"] or "",
            "ecc_no": row["ecc_no"] or "",
            "same_as_billing": bool(row["same_as_billing"]),
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_shipping_details(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "fields": [
                "customer",
                "name",
                "address"
            ]
        })

    data = request.data.copy()

    # 🔥 SAME AS BILLING LOGIC
    if data.get("is_same_as_billing"):
        billing = CustomerBillingDetails.objects.filter(
            customer_id=data.get("customer"),
            is_delete=False
        ).first()

        if billing:
            data.update({
                "name": billing.name,
                "address": billing.address,
                "country": billing.country.id if billing.country else None,
                "state": billing.state.id if billing.state else None,
                "city": billing.city.id if billing.city else None,
                "contact_name": billing.contact_name,
                "contact_no": billing.contact_no,
                "gst_no": billing.gst_no,
                "gst_status": billing.gst_status,
                "ecc_no": billing.ecc_no,
            })

    serializer = CustomerShippingDetailsSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Shipping created successfully",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_shipping_details(request, pk):
    try:
        obj = CustomerShippingDetails.objects.get(pk=pk)
    except CustomerShippingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = CustomerShippingDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_shipping_details(request, pk):
    try:
        obj = CustomerShippingDetails.objects.get(pk=pk)
    except CustomerShippingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# DOCUMENT VIEWS
@api_view(['GET'])
def list_documents(request):
    customer_id = request.GET.get("customer_id")
    params = []
    where_clause = "WHERE d.is_delete = 0"
    if customer_id:
        where_clause += " AND c.id = %s"
        params.append(customer_id)

    query = f"""
        SELECT
            d.shipping_details_id AS id,
            c.customer_name AS customer,
            c.id AS customer_id,
            d.type AS document_type,
            NULL AS document_type_id,
            d.type AS document_name,
            d.file_attach AS file
        FROM customer_document_upload d
        LEFT JOIN customer_profile c
            ON c.unique_id = d.customer_profile_unique_id
        {where_clause}
        ORDER BY d.shipping_details_id DESC
    """

    with closing(connections[_masters_db_alias()].cursor()) as cursor:
        cursor.execute(query, params)
        rows = _fetch_all_dicts(cursor)

    data = []
    for row in rows:
        data.append({
            "id": row["id"],
            "customer": row["customer"] or "",
            "customer_id": row["customer_id"],
            "document_type": row["document_type"] or "",
            "document_type_id": row["document_type_id"],
            "document_name": row["document_name"] or "",
            "file": row["file"] or "",
        })

    return Response({"data": data})


@api_view(['GET', 'POST'])
def create_document(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "fields": [
                "customer",
                "document_type",
                "document_name",
                "file"
            ]
        })

    serializer = CustomerDocumentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Document created successfully",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
def toggle_document(request, pk):
    try:
        obj = CustomerDocument.objects.get(pk=pk)
    except CustomerDocument.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# LIST
@api_view(['GET'])
def list_suppliers(request):
    queryset = SupplierProfile.objects.using(_masters_db_alias()).filter(is_delete=False)
    search = request.GET.get("search", "").strip()
    if search:
        queryset = queryset.filter(
            Q(vendor_name__icontains=search)
            | Q(phone_no__icontains=search)
            | Q(email_id__icontains=search)
            | Q(address__icontains=search)
        )

    data = []
    for i, obj in enumerate(queryset, start=1):
        data.append({
            "id": obj.pk,
            "sno": i,
            "vendor_name": obj.vendor_name,
            "group": "",
            "phone": obj.phone_no,
            "email_id": obj.email_id,
            "address": obj.address,
            "gst": obj.gst_no,
            "status": obj.is_active
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_supplier(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["vendor_name"]
        })

    data = request.data.copy()
    project_id = data.get("project")
    if project_id and not Project.objects.using(_masters_db_alias()).filter(pk=project_id).exists():
        return Response({
            "project": [f"Project with pk '{project_id}' does not exist."]
        }, status=400)

    serializer = SupplierProfileSerializer(data=data)
    if serializer.is_valid():
        supplier = SupplierProfile.objects.using(_masters_db_alias()).create(
            **serializer.validated_data
        )
        response_serializer = SupplierProfileSerializer(supplier)
        return Response({
            "message": "Supplier created successfully",
            "data": response_serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['GET', 'PUT', 'PATCH'])
def update_supplier(request, pk):
    try:
        obj = SupplierProfile.objects.using(_masters_db_alias()).get(pk=pk)
    except SupplierProfile.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    if request.method == 'GET':
        serializer = SupplierProfileSerializer(obj)
        return Response(serializer.data)

    serializer = SupplierProfileSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_supplier(request, pk):
    try:
        obj = SupplierProfile.objects.using(_masters_db_alias()).get(pk=pk)
    except SupplierProfile.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


@api_view(['GET'])
def list_supplier_contact_persons(request):
    queryset = SupplierContactPerson.objects.filter(is_delete=False)
    supplier_id = request.GET.get("supplier_id")
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    data = []
    for i, obj in enumerate(queryset, start=1):
        data.append({
            "sno": i,
            "id": obj.id,
            "supplier_id": obj.supplier.id if obj.supplier else None,
            "supplier_name": obj.supplier.vendor_name if obj.supplier else "",
            "person_name": obj.person_name,
            "designation": obj.designation,
            "email": obj.email,
            "mobile_no": obj.mobile_no,
            "landline": obj.landline,
            "department": obj.department,
            "status": obj.is_active,
        })

    return Response({"data": data})


@api_view(['GET', 'POST'])
def create_supplier_contact_person(request):
    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["supplier", "person_name"]
        })

    serializer = SupplierContactPersonSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Contact person created",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


@api_view(['PUT', 'PATCH'])
def update_supplier_contact_person(request, pk):
    try:
        obj = SupplierContactPerson.objects.get(pk=pk)
    except SupplierContactPerson.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = SupplierContactPersonSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
def toggle_supplier_contact_person(request, pk):
    try:
        obj = SupplierContactPerson.objects.get(pk=pk)
    except SupplierContactPerson.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# LIST
@api_view(['GET'])
def list_supplier_statutory(request):
    queryset = SupplierStatutoryDetails.objects.filter(is_delete=False)
    supplier_id = request.GET.get("supplier_id")
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    data = []
    for obj in queryset:
        data.append({
            "id": obj.id,
            "supplier": obj.supplier.id,
            "supplier_name": obj.supplier.vendor_name,

            "ecc_no": obj.ecc_no,
            "commissionerate": obj.commissionerate,
            "division": obj.division,
            "range": obj.range,

            "cst_no": obj.cst_no,
            "tin_no": obj.tin_no,
            "service_tax_no": obj.service_tax_no,
            "iec_code": obj.iec_code,

            "cin_no": obj.cin_no,
            "tan_no": obj.tan_no,
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_supplier_statutory(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["supplier"]
        })

    serializer = SupplierStatutoryDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Statutory details created",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_supplier_statutory(request, pk):
    try:
        obj = SupplierStatutoryDetails.objects.get(pk=pk)
    except SupplierStatutoryDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = SupplierStatutoryDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_supplier_statutory(request, pk):
    try:
        obj = SupplierStatutoryDetails.objects.get(pk=pk)
    except SupplierStatutoryDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})

    # LIST
@api_view(['GET'])
def list_supplier_accounts(request):
    queryset = SupplierAccountDetails.objects.filter(is_delete=False)
    supplier_id = request.GET.get("supplier_id")
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    data = []
    for i, obj in enumerate(queryset, start=1):
        data.append({
            "id": obj.id,
            "supplier": obj.supplier.id,
            "bank_name": obj.bank_name,
            "account_no": obj.account_no,
            "account_holder_name": obj.account_holder_name,
            "ifsc_code": obj.ifsc_code,
            "contact_no": obj.contact_no,
            "bank_address": obj.bank_address,
            "swift_code": obj.swift_code
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_supplier_account(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": [
                "supplier",
                "bank_name",
                "account_no",
                "account_holder_name",
                "ifsc_code"
            ]
        })

    serializer = SupplierAccountDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Account details created",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_supplier_account(request, pk):
    try:
        obj = SupplierAccountDetails.objects.get(pk=pk)
    except SupplierAccountDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = SupplierAccountDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_supplier_account(request, pk):
    try:
        obj = SupplierAccountDetails.objects.get(pk=pk)
    except SupplierAccountDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})


# LIST
@api_view(['GET'])
def list_supplier_billing(request):
    queryset = SupplierBillingDetails.objects.filter(is_delete=False)
    supplier_id = request.GET.get("supplier_id")
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    data = []
    for obj in queryset:
        data.append({
            "id": obj.id,
            "supplier": obj.supplier.id,
            "supplier_name": obj.supplier.vendor_name,
            "name": obj.name,
            "address": obj.address,
            "country": obj.country.id if obj.country else None,
            "country_name": obj.country_name,
            "state": obj.state.id if obj.state else None,
            "state_name": obj.state_name,
            "city": obj.city.id if obj.city else None,
            "city_name": obj.city_name,
            "contact_name": obj.contact_name,
            "contact_no": obj.contact_no,
            "gst_no": obj.gst_no,
            "gst_status": obj.gst_status,
            "ecc_no": obj.ecc_no,
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_supplier_billing(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["supplier", "name", "address"]
        })

    serializer = SupplierBillingDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Billing details created",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_supplier_billing(request, pk):
    try:
        obj = SupplierBillingDetails.objects.get(pk=pk)
    except SupplierBillingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = SupplierBillingDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_supplier_billing(request, pk):
    try:
        obj = SupplierBillingDetails.objects.get(pk=pk)
    except SupplierBillingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})

# LIST
@api_view(['GET'])
def list_supplier_shipping(request):
    queryset = SupplierShippingDetails.objects.filter(is_delete=False)
    supplier_id = request.GET.get("supplier_id")
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    data = []
    for obj in queryset:
        data.append({
            "id": obj.id,
            "supplier": obj.supplier.id,
            "name": obj.name,
            "address": obj.address,
            "country": obj.country.id if obj.country else None,
            "country_name": obj.country_name,
            "state": obj.state.id if obj.state else None,
            "state_name": obj.state_name,
            "city": obj.city.id if obj.city else None,
            "city_name": obj.city_name,
            "contact_name": obj.contact_name,
            "contact_no": obj.contact_no,
            "gst_no": obj.gst_no,
            "gst_status": obj.gst_status,
            "ecc_no": obj.ecc_no,
            "same_as_billing": obj.is_same_as_billing
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_supplier_shipping(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["supplier"]
        })

    data = request.data.copy()

    # 🔥 SAME AS BILLING LOGIC
    if data.get("is_same_as_billing"):
        billing = SupplierBillingDetails.objects.filter(
            supplier_id=data.get("supplier"),
            is_delete=False
        ).first()

        if billing:
            data.update({
                "name": billing.name,
                "address": billing.address,
                "country": billing.country.id if billing.country else None,
                "state": billing.state.id if billing.state else None,
                "city": billing.city.id if billing.city else None,
                "contact_name": billing.contact_name,
                "contact_no": billing.contact_no,
                "gst_no": billing.gst_no,
                "gst_status": billing.gst_status,
                "ecc_no": billing.ecc_no,
            })

    serializer = SupplierShippingDetailsSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Shipping created",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# UPDATE
@api_view(['PUT', 'PATCH'])
def update_supplier_shipping(request, pk):
    try:
        obj = SupplierShippingDetails.objects.get(pk=pk)
    except SupplierShippingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = SupplierShippingDetailsSerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Updated successfully",
            "data": serializer.data
        })

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_supplier_shipping(request, pk):
    try:
        obj = SupplierShippingDetails.objects.get(pk=pk)
    except SupplierShippingDetails.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})

# LIST
@api_view(['GET'])
def list_supplier_documents(request):
    queryset = SupplierDocuments.objects.filter(is_delete=False)
    supplier_id = request.GET.get("supplier_id")
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    data = []
    for obj in queryset:
        data.append({
            "id": obj.id,
            "supplier": obj.supplier.id,
            "document_type": obj.document_type,
            "file": obj.file.url if obj.file else None,
            "document_name": obj.file.name.split("/")[-1] if obj.file else "",
        })

    return Response({"data": data})


# CREATE
@api_view(['GET', 'POST'])
def create_supplier_document(request):

    if request.method == 'GET':
        return Response({
            "message": "Send POST request",
            "required_fields": ["supplier", "document_type", "file"]
        })

    serializer = SupplierDocumentsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Document uploaded",
            "data": serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)


# DELETE
@api_view(['DELETE'])
def toggle_supplier_document(request, pk):
    try:
        obj = SupplierDocuments.objects.get(pk=pk)
    except SupplierDocuments.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    obj.is_delete = True
    obj.save()

    return Response({"message": "Deleted successfully"})
