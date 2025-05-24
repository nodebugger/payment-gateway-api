from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Payment

class PaymentTests(APITestCase):

    def test_create_payment(self):
        url = reverse('create-payment')
        data = {
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "amount": 1000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment', response.data)

    def test_retrieve_payment(self):
        # First create a payment
        payment = Payment.objects.create(
            customer_name="Jane Doe",
            customer_email="jane@example.com",
            amount=5000
        )
        url = reverse('payment-detail', kwargs={"id": str(payment.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment']['customer_name'], "Jane Doe")
