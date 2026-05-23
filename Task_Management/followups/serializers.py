from rest_framework import serializers

from .models import TaskFollowups


class TaskFollowupsSerializer(serializers.ModelSerializer):

    class Meta:

        model = TaskFollowups

        fields = '__all__'