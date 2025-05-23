import uuid
from django.db import models

# Create your models here.
class Payment(models.Model):
    # STATUS_CHOICES = [
    #     ('pending', 'Pending'),
    #     ('completed', 'Completed'),
    #     ('failed', 'Failed'),
    # ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.customer_name} - {self.amount}"