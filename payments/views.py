from django.shortcuts import render
from django.conf import settings
import requests

from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import generics, status
from .models import Payment
from .serializers import PaymentSerializer


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
            "callback_url": "http://127.0.0.1:8000/api/v1/payments/success/"
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
            "status": "success",
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
    def post(self, request):

        reference = request.data.get('reference')
        if not reference:
            return Response({"error": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        result = response.json()
        if result['data']['status'] == 'success':
            try:
                payment = Payment.objects.get(reference=reference)
                payment.paid = True
                payment.save()
                return Response({
                    "message": "Payment verified successfully",
                    "payment_status": result['data']['status']
                })
            except Payment.DoesNotExist:
                return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Payment not successful yet"}, status=status.HTTP_200_OK)