from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter


DATATABLE_PARAMETERS = [
    OpenApiParameter(
        name="draw",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Datatable draw counter.",
    ),
    OpenApiParameter(
        name="start",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Zero-based row offset.",
    ),
    OpenApiParameter(
        name="length",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Number of rows to return.",
    ),
    OpenApiParameter(
        name="search[value]",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=False,
        description="Datatable search text.",
    ),
]


SEARCH_PARAMETER = OpenApiParameter(
    name="search",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Search text.",
)


def query_int_parameter(name, description, required=False):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
    )


def query_str_parameter(name, description, required=False):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
    )


def query_date_parameter(name, description, required=False):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.DATE,
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
    )
