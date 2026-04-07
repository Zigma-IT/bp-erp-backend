from django.urls import path
from .views import PurchaseOrderCreateView, PurchaseOrderListView, PurchaseOrderLevel1ListView, PurchaseOrderLevel2ListView

urlpatterns = [
    path('purchase_order/create/', PurchaseOrderCreateView.as_view()),
    path('purchase_order/list/', PurchaseOrderListView.as_view()),
    path('po/level_1/list/', PurchaseOrderLevel1ListView.as_view()),
    path('po/level_2/list/', PurchaseOrderLevel2ListView.as_view()),
]