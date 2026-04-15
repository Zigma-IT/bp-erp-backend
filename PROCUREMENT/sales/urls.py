from django.urls import path

from . import views

# Sales order endpoints
sales_order_patterns = [
    path("sales-orders/", views.sales_order_list, name="sales-order-list"),
    path("sales-orders/<int:pk>/", views.sales_order_detail, name="sales-order-detail"),
]

# Combine all patterns
urlpatterns = sales_order_patterns
