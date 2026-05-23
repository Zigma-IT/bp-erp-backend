from rest_framework import serializers
from .models import TaskCategory , TaskSubCategory , PriorityCreation , ProblemType , RemarkCreation


class TaskCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskCategory
        fields = '__all__'
        

class TaskSubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskSubCategory
        fields = "__all__"


class PriorityCreationSerializer(serializers.ModelSerializer):

    class Meta:

        model = PriorityCreation

        fields = "__all__"
class ProblemTypeSerializer(serializers.ModelSerializer):

    class Meta:

        model = ProblemType

        fields = "__all__"

class RemarkCreationSerializer(serializers.ModelSerializer):

    class Meta:

        model = RemarkCreation

        fields = "__all__"




