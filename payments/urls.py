from django.urls import path
from .views import PaymentCreateView, PaymentDetailView, VerifyPayment

urlpatterns = [
    path('v1/payments/', PaymentCreateView.as_view(), name='create-payment'),
    path('v1/payments/<str:id>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('verify/', VerifyPayment.as_view(), name='payment-verify'),
]