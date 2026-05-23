from rest_framework import serializers

from tasks.models import TaskCreation
from followups.models import TaskFollowups


class TaskReportSerializer(serializers.ModelSerializer):

    latest_comment = serializers.SerializerMethodField()

    comment_date = serializers.SerializerMethodField()

    assigned_by = serializers.SerializerMethodField()

    remark = serializers.SerializerMethodField()

    class Meta:

        model = TaskCreation

        fields = [

            'id',
            'unique_id',
            'task_code',
            'department_id',
            'task_category_id',
            'company_id',
            'project_id',
            'assigned_to',
            'priority',
            'target_date',
            'description',
            'status',
            'created_date',

            'latest_comment',
            'comment_date',
            'assigned_by',
            'remark',
        ]

    def _get_followup(self, obj):

        return TaskFollowups.objects.filter(
            task_no=obj.task_code,
            is_delete=False
        ).order_by('-id').first()

    def get_latest_comment(self, obj):

        followup = self._get_followup(obj)

        if followup:
            return followup.tag_remark

        return None

    def get_comment_date(self, obj):

        followup = self._get_followup(obj)

        if followup:
            return followup.tagged_datetime

        return None

    def get_assigned_by(self, obj):

        followup = self._get_followup(obj)

        if followup:
            return followup.tagged_by

        return None

    def get_remark(self, obj):

        followup = self._get_followup(obj)

        if followup:
            return followup.remarks_type

        return None
