from django.db import models
from users.models import User
from django.utils import timezone

# Create your models here.

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    date = models.DateTimeField(default=timezone.now)
    open_date = models.DateTimeField()
    close_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    max_quantity = models.PositiveIntegerField(default=0)
    ticket_price = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Event"
    
    def __str__(self):
        return self.title


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_datetime = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    

    class Meta:
        db_table = "Order"    

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
    

class Ticket(models.Model):
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket')
    customer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket')
    # name = models.CharField(max_length=100) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets", null=True, blank=True)


    class Meta:
        db_table = "Ticket"

    def __str__(self):
        return f"{self.customer_id.username} - {self.event.title}"
    
    