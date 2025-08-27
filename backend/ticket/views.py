from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
import time

from .serializers import EventSerializer, TicketOrderSerializer, OrderSerializer
from .models import Event, Ticket, Order
from utils.redis import myredis

from users.models import User

import pandas as pd


class EventGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)

        data = serializer.data
        for event in data:
            event_id = event["id"]
            cache_key = f"event:{event_id}:tickets_count"

            tickets_count = myredis.get(cache_key)
            if tickets_count is None:
                tickets_count = Ticket.objects.filter(event_id=event_id).count()
                myredis.set(cache_key, tickets_count)

            event["tickets_bought"] = tickets_count

        return Response(data, status=status.HTTP_200_OK)


class EventGetSingleView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EventSerializer(event)
        data = serializer.data

        cache_key = f"event:{event.id}:tickets_count"
        tickets_count = myredis.get(cache_key)
        if tickets_count is None:
            tickets_count = Ticket.objects.filter(event=event).count()
            myredis.set(cache_key, tickets_count)

        data["tickets_bought"] = tickets_count
        return Response(data, status=status.HTTP_200_OK)


class TicketPostView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TicketOrderSerializer(
            data=request.data, 
            context={"request": request}
        )
        
        if serializer.is_valid():
            try:
                ticket_data = serializer.validated_data
                event_id = ticket_data["event"]  # assumes serializer has event FK
                
                cache_key = f"event:{event_id}:tickets_count"

                # Read from Redis first
                current_count = myredis.get(cache_key)
                event = Event.objects.get(pk=event_id)
                if current_count is None:
                    # Initialize cache only once, from DB at startup
                    current_count = event.ticket_count
                    myredis.set(cache_key, current_count)

                current_count = int(current_count)

                # Check limit against Redis counter
                if current_count >= event.max_quantity:
                    return Response(
                        {"error": "Max tickets reached for this event"},
                        status=status.HTTP_409_CONFLICT,   # changed from 400 to 409
                    )

                # Atomically increment in Redis to "reserve" a ticket
                myredis.incr(cache_key)

                # Save pending info in Redis (optional, useful for debugging / reconciliation)
                pending_key = f"pending:ticket:{request.user.id}:{event.id}"
                myredis.set(pending_key, {"user": request.user.id, "event": event.id}, timeout=120)

                # Simulate payment delay
                time.sleep(1)

                # Save to DB
                result = serializer.save()
                ticket = result["ticket"]

                return Response(
                    {
                        "ticket_id": ticket.id,
                        "order_id": result["order"].id,
                        "message": "Ticket and order created successfully"
                    },
                    status=status.HTTP_201_CREATED,
                )
            
            except Exception as e:
                return Response(
                    {"error": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOrdersAndTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related("tickets__event")
        serializer = OrderSerializer(orders, many=True)
        return Response({"orders": serializer.data}, status=status.HTTP_200_OK)
    
    
    
class FileUploadView(APIView):
    parser_classes = [FileUploadParser]
    permission_classes = [AllowAny]

    def post(self, request, filename, format=None):
        file_obj = request.data['file']

        # Validate MIME type
        if file_obj.content_type not in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]:
            return Response(
                {"error": "Only Excel files (.xlsx, .xls) are supported."},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        # Validate content
        try:
            df = pd.read_excel(file_obj)
            
        except Exception as e:
            return Response(
                {"error": f"Invalid Excel file: {str(e)}"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        serializer = TicketOrderSerializer(data=df.to_dict(), context={"request": request})
        if serializer.is_valid():
            serializer.save()
    
            return Response({"message": "File uploaded successfully."}, status=status.HTTP_201_CREATED)
        
        return Response({"message": "File uploaded successfully."}, status=status.HTTP_400_BAD_REQUEST)
