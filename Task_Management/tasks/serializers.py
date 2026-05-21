from rest_framework import serializers

from .models import TaskCreation,SelfTask


class TaskCreationSerializer(serializers.ModelSerializer):

    class Meta:

        model = TaskCreation

        fields = '__all__'



class SelfTaskSerializer(serializers.ModelSerializer):

    class Meta:

        model = SelfTask

        fields = '__all__'