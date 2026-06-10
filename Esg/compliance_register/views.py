from datetime import date
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    ESGComplianceRegister,
    ESGComplianceEntry,
    ESGComplianceHistory,
    InsuranceRegister,
    InsuranceRegisterDetail,
)
from .serializers import (
    ESGComplianceRegisterSerializer,
    ESGComplianceEntrySerializer,
    ESGComplianceHistorySerializer,
    InsuranceRegisterSerializer,
    InsuranceRegisterDetailSerializer,
)


# ── Unique-ID generators ─────────────────────────────────────────────

def _generate_type_id():
    year = date.today().year
    count = ESGComplianceRegister.objects.filter(
        unique_id__startswith=f"CTYPE/{year}/"
    ).count()
    return f"CTYPE/{year}/{str(count + 1).zfill(3)}"


def _generate_entry_id(company_code: str = "GEN"):
    year = date.today().year
    prefix = f"CENTRY/{year}/{company_code}/"
    count = ESGComplianceEntry.objects.filter(
        unique_id__startswith=prefix
    ).count()
    return f"{prefix}{str(count + 1).zfill(3)}"


def _generate_insurance_id():
    year = date.today().year
    count = InsuranceRegister.objects.filter(
        unique_id__startswith=f"INS/{year}/"
    ).count()
    return f"INS/{year}/{str(count + 1).zfill(3)}"


# ── Compliance TYPE views ────────────────────────────────────────────

class ESGComplianceRegisterListCreateAPIView(generics.ListCreateAPIView):
    queryset = ESGComplianceRegister.objects.filter(is_delete=False)
    serializer_class = ESGComplianceRegisterSerializer

    def perform_create(self, serializer):
        serializer.save(unique_id=_generate_type_id())


class ESGComplianceRegisterRetrieveAPIView(generics.RetrieveAPIView):
    queryset = ESGComplianceRegister.objects.filter(is_delete=False)
    serializer_class = ESGComplianceRegisterSerializer


class ESGComplianceRegisterUpdateAPIView(generics.UpdateAPIView):
    queryset = ESGComplianceRegister.objects.filter(is_delete=False)
    serializer_class = ESGComplianceRegisterSerializer


class ESGComplianceRegisterDeleteAPIView(generics.DestroyAPIView):
    queryset = ESGComplianceRegister.objects.filter(is_delete=False)
    serializer_class = ESGComplianceRegisterSerializer

    def perform_destroy(self, instance):
        instance.is_delete = True
        instance.save()


# APIView-based TYPE views (kept for backward compat)

class ESGComplianceCreateAPIView(APIView):
    def post(self, request):
        serializer = ESGComplianceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(unique_id=_generate_type_id())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ESGComplianceListAPIView(APIView):
    def get(self, request):
        queryset = ESGComplianceRegister.objects.filter(is_delete=False)
        serializer = ESGComplianceRegisterSerializer(queryset, many=True)
        return Response(serializer.data)


class ESGComplianceRetrieveAPIView(APIView):
    def get(self, request, id):
        try:
            obj = ESGComplianceRegister.objects.get(id=id, is_delete=False)
        except ESGComplianceRegister.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ESGComplianceRegisterSerializer(obj).data)


class ESGComplianceUpdateAPIView(APIView):
    def put(self, request, id):
        try:
            obj = ESGComplianceRegister.objects.get(id=id, is_delete=False)
        except ESGComplianceRegister.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ESGComplianceRegisterSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ESGComplianceDeleteAPIView(APIView):
    def delete(self, request, id):
        try:
            obj = ESGComplianceRegister.objects.get(id=id, is_delete=False)
        except ESGComplianceRegister.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_delete = True
        obj.save()
        return Response({"message": "Deleted Successfully"})


# ── Compliance ENTRY views ───────────────────────────────────────────

class ESGComplianceEntryListAPIView(APIView):
    def get(self, request):
        queryset = ESGComplianceEntry.objects.filter(is_delete=False)
        serializer = ESGComplianceEntrySerializer(queryset, many=True)
        return Response(serializer.data)

class ESGComplianceEntryCreateAPIView(APIView):
    def post(self, request):

        company_code = request.data.get(
            "company_code",
            "GEN"
        )

        serializer = ESGComplianceEntrySerializer(
            data=request.data
        )

        if serializer.is_valid():

            entry = serializer.save(
                unique_id=_generate_entry_id(company_code)
            )

            ESGComplianceHistory.objects.create(
                compliance_entry=entry,
                issue_date=entry.issue_date,
                expiry_date=entry.expiry_date,
                notify_days=entry.notify_days,
                status=entry.status.lower(),
                responsible_person=entry.responsible_person,
                reference_no=entry.reference_no,
                remarks=entry.remarks
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ESGComplianceEntryBulkCreateAPIView(APIView):

    def post(self, request):

        entries = request.data.get("entries", [])

        company_code = request.data.get(
            "company_code",
            "GEN"
        )

        if not entries:

            return Response(
                {
                    "detail": "At least one entry is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []

        errors = []

        for idx, entry in enumerate(entries):

            serializer = ESGComplianceEntrySerializer(
                data=entry
            )

            if serializer.is_valid():

                entry_obj = serializer.save(
                    unique_id=_generate_entry_id(
                        company_code
                    )
                )

                # Create History Record
                ESGComplianceHistory.objects.create(
                    compliance_entry=entry_obj,
                    issue_date=entry_obj.issue_date,
                    expiry_date=entry_obj.expiry_date,
                    notify_days=entry_obj.notify_days,
                    status=entry_obj.status.lower(),
                    responsible_person=entry_obj.responsible_person,
                    reference_no=entry_obj.reference_no,
                    remarks=entry_obj.remarks,
                )

                created.append(
                    serializer.data
                )

            else:

                errors.append(
                    {
                        "row": idx + 1,
                        "errors": serializer.errors
                    }
                )

        if errors:

            return Response(
                {
                    "detail": "Validation failed.",
                    "errors": errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "created": created
            },
            status=status.HTTP_201_CREATED
        )

class ESGComplianceEntryRetrieveAPIView(APIView):
    def get(self, request, id):
        try:
            obj = ESGComplianceEntry.objects.get(id=id, is_delete=False)
        except ESGComplianceEntry.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ESGComplianceEntrySerializer(obj).data)


class ESGComplianceEntryUpdateAPIView(APIView):
    def put(self, request, id):
        try:
            obj = ESGComplianceEntry.objects.get(id=id, is_delete=False)
        except ESGComplianceEntry.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ESGComplianceEntrySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ESGComplianceEntryDeleteAPIView(APIView):
    def delete(self, request, id):
        try:
            obj = ESGComplianceEntry.objects.get(id=id, is_delete=False)
        except ESGComplianceEntry.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_delete = True
        obj.save()
        return Response({"message": "Deleted Successfully"})


class ESGComplianceHistoryRetrieveAPIView(APIView):
    def get(self, request, id):
        try:
            obj = ESGComplianceHistory.objects.get(id=id)
        except ESGComplianceHistory.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ESGComplianceHistorySerializer(obj).data)


class ESGComplianceHistoryListAPIView(APIView):
    def get(self, request, entry_id):
        queryset = ESGComplianceHistory.objects.filter(compliance_entry_id=entry_id).order_by("-id")
        serializer = ESGComplianceHistorySerializer(queryset, many=True)
        return Response(serializer.data)


class ESGComplianceRenewAPIView(APIView):
    def post(self, request, id):
        try:
            entry = ESGComplianceEntry.objects.get(id=id, is_delete=False)
        except ESGComplianceEntry.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data["compliance_entry"] = entry.id

        serializer = ESGComplianceHistorySerializer(data=data)
        if serializer.is_valid():
            history = serializer.save()
            entry.issue_date = history.issue_date
            entry.expiry_date = history.expiry_date
            entry.notify_days = history.notify_days
            entry.status = history.status.title()
            entry.responsible_person = history.responsible_person
            entry.reference_no = history.reference_no
            entry.remarks = history.remarks
            entry.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Insurance Register views ─────────────────────────────────────────

class InsuranceRegisterCreateAPIView(APIView):
    def post(self, request):
        serializer = InsuranceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(unique_id=_generate_insurance_id())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InsuranceRegisterListAPIView(APIView):
    def get(self, request):
        queryset = InsuranceRegister.objects.filter(is_delete=False)
        serializer = InsuranceRegisterSerializer(queryset, many=True)
        return Response(serializer.data)


class InsuranceRegisterRetrieveAPIView(APIView):
    def get(self, request, id):
        try:
            obj = InsuranceRegister.objects.get(id=id, is_delete=False)
        except InsuranceRegister.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(InsuranceRegisterSerializer(obj).data)


class InsuranceRegisterUpdateAPIView(APIView):
    def put(self, request, id):
        try:
            obj = InsuranceRegister.objects.get(id=id, is_delete=False)
        except InsuranceRegister.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = InsuranceRegisterSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InsuranceRegisterDeleteAPIView(APIView):
    def delete(self, request, id):
        try:
            obj = InsuranceRegister.objects.get(id=id, is_delete=False)
        except InsuranceRegister.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_delete = True
        obj.save()
        return Response({"message": "Deleted Successfully"})
