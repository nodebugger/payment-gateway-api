from django.shortcuts import render, get_object_or_404
from django.conf import settings
import requests

from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import generics, status
from .models import Payment
from .serializers import PaymentSerializer

from django.http import HttpResponse
from django.urls import reverse


# POST /api/v1/payments/
class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()


        # Paystack Integration
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "email": payment.customer_email,
            "amount": int(payment.amount * 100),
            "reference": f"{payment.id}", #To use DB ID as reference
            "callback_url": request.build_absolute_uri(
                reverse('payment-detail', kwargs={"id": str(payment.id)})
                )
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=data,
            headers=headers
        )
        
        if response.status_code != 200:
            return Response({"error": "Payment initialization failed"}, status=500)

        paystack_data = response.json()

        reference = paystack_data['data']['reference']
        payment.reference = reference
        payment.save()

        return Response({
            "payment": serializer.data,
            "status": "pending",
            "message": "Payment initialized. Redirect user to authorization_url to complete payment.",
            "authorization_url": paystack_data["data"]["authorization_url"]
        }, status=status.HTTP_201_CREATED)

# GET /api/v1/payments/<id>
class PaymentDetailView(generics.RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        payment = self.get_object()
        serializer = self.get_serializer(payment)

        return Response({
            "payment": serializer.data,
            "status": "success",
            "message": "Payment details retrieved successfully."
        }, status=status.HTTP_200_OK)

# Verifying Payment
class VerifyPayment(APIView):
    queryset = Payment.objects.all()
    def get(self, request):
        reference = request.queryset.get('reference')
        if not reference:
            return Response({"error": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        print("Paystack Secret Key:", settings.PAYSTACK_SECRET_KEY)

        url = f"https://api.paystack.co/transaction/verify/{reference}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        result = response.json()

        if not result.get("status"):
            return Response({"error": "Transaction not successful"}, status=status.HTTP_400_BAD_REQUEST)

        data = result["data"]
        status_from_paystack = data["status"]

        # Update the payment record if it exists
        try:
            payment = Payment.objects.get(reference=reference)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found in local database"}, status=status.HTTP_404_NOT_FOUND)

        payment.paid = True
        payment.save()
        
        return Response({
            "message": "Payment verified successfully",
            "payment_status": status_from_paystack,
            "payment": {
                "id": str(payment.id),
                "email": payment.customer_email,
                "amount": payment.amount,
                "reference": payment.reference,
                "verified": payment.paid,
            }
        }, status=status.HTTP_200_OK)

def home(request):
    html = f"""
    <html>
        <head><title>Payment Gateway API</title></head>
        <body>
            <h1>Welcome to the Payment Gateway API</h1>
            <ul>
                <li><a href="{reverse('create-payment')}">Create Payment</a></li>
            </ul>
        </body>
    </html>
    """
    return HttpResponse(html)


def payment_success(request):
    return HttpResponse("<h2>Payment was successful!</h2>")