from django.urls import path
from .views import PaymentCreateView, PaymentDetailView, VerifyPayment, payment_success

urlpatterns = [
    path('', PaymentCreateView.as_view(), name='create-payment'),
    path('<str:id>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('/api/v1/payments/verify/', VerifyPayment.as_view(), name='payment-verify'),
    path('success/', payment_success, name='payment-success'),
]