from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser

from .serializers import EventSerializer, TicketOrderSerializer, OrderSerializer
from .models import Event, Ticket, Order

from users.models import User
from django.db.models import Count

import pandas as pd


class EventGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.annotate(ticket_count=Count('ticket'))
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class EventGetSingleView(APIView):
    # permission_classes = [AllowAny]
    
    def get(self, request, pk):
        events = Event.objects.annotate(ticket_count=Count('ticket')).get(pk=pk)
        serializer = EventSerializer(events)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class TicketPostView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TicketOrderSerializer(data=request.data, context={"request": request})
        print("HIHIHIHIIHIHIHIHIH1")
        
        if serializer.is_valid():
            print("HIHIHIHIIHIHIHIHIH2")
            
            result = serializer.save()
            return Response(
                {
                    "ticket_id": result["ticket"].id,
                    "order_id": result["order"].id,
                    "message": "Ticket and order created successfully"
                },
                status=status.HTTP_201_CREATED,
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
