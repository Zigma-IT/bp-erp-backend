# """Reports app does not define standalone database models.

# This app serves read-only report APIs by querying tables from other apps.
# """
from django.db import models

# Purchase Requisition Approval Level 1
LEVEL1_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)
"""Approvals app does not define standalone database models."""

level1_status = models.CharField(
    max_length=20,
    choices=LEVEL1_STATUS,
    default='pending'
)

level1_approved_by = models.ForeignKey(
    'auth.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='pr_level1_approved'
)

level1_approved_at = models.DateTimeField(null=True, blank=True)
level1_remarks = models.TextField(blank=True, null=True)

# Purhcase Requisition level 2
LEVEL2_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

level2_status = models.CharField(
    max_length=20,
    choices=LEVEL2_STATUS,
    default='pending'
)

level2_approved_by = models.ForeignKey(
    'auth.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='pr_level2_approved'
)

level2_approved_at = models.DateTimeField(null=True, blank=True)
level2_remarks = models.TextField(null=True, blank=True)


# GRN Approval Level 1
GRN_LEVEL1_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

level1_status = models.CharField(
    max_length=20,choices=GRN_LEVEL1_STATUS,default='pending')

level1_approved_by = models.ForeignKey(
    'auth.User',on_delete=models.SET_NULL,null=True,blank=True,related_name='grn_level1_approved')

level1_approved_at = models.DateTimeField(null=True, blank=True)
level1_remarks = models.TextField(null=True, blank=True)

# GRN Approval Level 2

GRN_LEVEL2_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

level2_status = models.CharField(
    max_length=20,
    choices=GRN_LEVEL2_STATUS,
    default='pending'
)

level2_checked_by = models.ForeignKey(
    'auth.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='grn_level2_checked'
)

level2_checked_at = models.DateTimeField(null=True, blank=True)
level2_remarks = models.TextField(null=True, blank=True)

# SRN Approval Level 1
SRN_APPROVAL_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

level1_status = models.CharField(
    max_length=20,
    choices=SRN_APPROVAL_STATUS,
    default='pending'
)

level1_approved_by = models.ForeignKey(
    'auth.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='srn_level1_approved'
)

level1_approved_at = models.DateTimeField(null=True, blank=True)
level1_remarks = models.TextField(null=True, blank=True)


# SRN Approval Level 2
level2_status = models.CharField(
    max_length=20,
    choices=SRN_APPROVAL_STATUS,
    null=True,
    blank=True
)

level2_approved_by = models.ForeignKey(
    'auth.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='srn_level2_approved'
)

level2_approved_at = models.DateTimeField(null=True, blank=True)
level2_remarks = models.TextField(null=True, blank=True)