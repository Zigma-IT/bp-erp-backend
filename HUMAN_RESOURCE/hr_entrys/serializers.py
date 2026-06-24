from rest_framework import serializers
from .models import ShiftCreation , ShiftRoster , WeekoffCreation , HolidayCreation , LeaveEntry


class ShiftCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShiftCreation
        fields = "__all__"


class ShiftRosterSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShiftRoster
        fields = "__all__"
        

class WeekoffCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = WeekoffCreation
        fields = "__all__"


class HolidayCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = HolidayCreation
        fields = "__all__"


class LeaveEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveEntry
        fields = "__all__"