from django.urls import path, re_path

from .views import EventGetView, EventGetSingleView, TicketPostView, UserOrdersAndTicketsView, FileUploadView

urlpatterns = [
    path("events", EventGetView.as_view()),
    path("events/<int:pk>/", EventGetSingleView.as_view()),
    path("ticket/", TicketPostView.as_view()),
    path("orders/", UserOrdersAndTicketsView.as_view(), name="user-orders"),
    re_path(r'^upload/(?P<filename>[^/]+)$', FileUploadView.as_view()),
]
