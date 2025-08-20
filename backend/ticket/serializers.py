from rest_framework import serializers
from .models import Event, Ticket, Order

class EventSerializer(serializers.ModelSerializer):
    ticket_count = serializers.IntegerField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'location', 'open_date', 'close_date', 'max_quantity', 'ticket_count']
        


class TicketSerializer(serializers.ModelSerializer):
    event = serializers.CharField(source="event.title")
    location = serializers.CharField(source="event.location")
    date = serializers.DateTimeField(source="event.date")

    class Meta:
        model = Ticket
        fields = ["id", "event", "location", "date", "price", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "total_amount", "unit_price", "status", "order_datetime", "tickets"]


class TicketOrderSerializer(serializers.Serializer):
    event = serializers.IntegerField()

    def create(self, validated_data):
        user = self.context["request"].user
        event_id = validated_data["event"]

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event_id": "Event not found."})

        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=1,  # one ticket per event
            unit_price=event.ticket_price,
            status="paid",
        )
        
        # Create ticket
        ticket = Ticket.objects.create(
            event=event,
            customer_id=user,
            price=event.ticket_price,
            order=order,
        )

        

        return {"ticket": ticket, "order": order}
