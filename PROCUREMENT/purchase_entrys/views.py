from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer


class PurchaseOrderCreateView(CreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    @extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            201: inline_serializer(
                name='PurchaseOrderCreateResponse',
                fields={'message': serializers.CharField()},
            )
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "PO Created"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderListView(ListAPIView):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.all().order_by('-created_at')

    @extend_schema(
        parameters=[
            OpenApiParameter(name='company', type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='project', type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='from_date', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='to_date', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='status', type=str, location=OpenApiParameter.QUERY),
        ]
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        company = self.request.GET.get('company')
        project = self.request.GET.get('project')
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')
        status_filter = self.request.GET.get('status')

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if from_date and to_date:
            queryset = queryset.filter(entry_date__range=[from_date, to_date])

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset
    

#Purchase Order Approvel level 1

from rest_framework.views import APIView
from django.db.models import F
from .models import PurchaseOrder


class PurchaseOrderLevel1ListView(APIView):

    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status_filter = request.GET.get('status')

        queryset = PurchaseOrder.objects.select_related(
            'company', 'project', 'supplier'
        )

        # Filters
        if from_date and to_date:
            queryset = queryset.filter(entry_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if status_filter and status_filter != "All":
            queryset = queryset.filter(status=status_filter)

        # 🚫 No JOIN → No Duplicate Rows
        queryset = queryset.order_by('-entry_date')

        # Lightweight fetch
        queryset = queryset.values(
            'id',
            'entry_date',
            'po_number',
            'total_basic_value',
            'gross_amount',
            'status',
            company_name=F('company__name'),
            project_name=F('project__name'),
            supplier_name=F('supplier__name'),
        )

        # Response format
        data = []
        for i, row in enumerate(queryset, start=1):
            data.append({
                "sno": i,
                "entry_date": row['entry_date'],
                "po_number": row['po_number'],
                "company_name": row['company_name'],
                "project_name": row['project_name'],
                "supplier_name": row['supplier_name'],
                "net_amount": float(row['total_basic_value']),
                "gross_amount": float(row['gross_amount']),
                "status": row['status']
            })

        return Response({
            "recordsTotal": len(data),
            "recordsFiltered": len(data),
            "data": data
        })
    

#Purchase order approvel level 2 & 3
from rest_framework.views import APIView
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from .models import PurchaseOrder


class PurchaseOrderLevel2ListView(APIView):

    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status_filter = request.GET.get('status')

        queryset = PurchaseOrder.objects.select_related(
            'company', 'project', 'supplier'
        ).select_related(
            'level1', 'level2'
        )

        # Filters
        if from_date and to_date:
            queryset = queryset.filter(entry_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        # ⚠️ Only Level-1 approved should come here
        queryset = queryset.filter(level1__status='approved')

        # Status filter for Level-2
        if status_filter and status_filter != "All":
            queryset = queryset.filter(level2__status=status_filter)

        queryset = queryset.annotate(
            appr_net_amount=Coalesce(F('level1__approved_net_amount'), Value(0)),
            appr_gross_amount=Coalesce(F('level1__approved_gross_amount'), Value(0)),
            lvl2_net_amount=Coalesce(F('level2__approved_net_amount'), Value(0)),
            lvl2_gross_amount=Coalesce(F('level2__approved_gross_amount'), Value(0)),
        )

        queryset = queryset.values(
            'id',
            'entry_date',
            'po_number',
            'total_basic_value',
            'gross_amount',
            'appr_net_amount',
            'appr_gross_amount',
            'lvl2_net_amount',
            'lvl2_gross_amount',
            company_name=F('company__name'),
            project_name=F('project__name'),
            supplier_name=F('supplier__name'),
        )

        data = []
        for i, row in enumerate(queryset, start=1):
            data.append({
                "sno": i,
                "entry_date": row['entry_date'],
                "po_number": row['po_number'],
                "company_name": row['company_name'],
                "project_name": row['project_name'],
                "supplier_name": row['supplier_name'],

                "net_amount": float(row['total_basic_value']),
                "gross_amount": float(row['gross_amount']),

                "appr_net_amount": float(row['appr_net_amount']),
                "appr_gross_amount": float(row['appr_gross_amount']),

                "lvl2_net_amount": float(row['lvl2_net_amount']),
                "lvl2_gross_amount": float(row['lvl2_gross_amount']),
            })

        return Response({
            "recordsTotal": len(data),
            "recordsFiltered": len(data),
            "data": data
        })