from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = Notification.objects.filter(
            recipient=request.user,
            tenant=request.user.tenant,
        ).order_by("-created_at")[:50]
        return Response(NotificationSerializer(qs, many=True).data)


class NotificationUnreadCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            tenant=request.user.tenant,
            is_read=False,
        ).count()
        return Response({"count": count})


class NotificationMarkReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.is_read = True
        notif.save()
        return Response({"detail": "Marked as read."})


class NotificationMarkAllReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            tenant=request.user.tenant,
            is_read=False,
        ).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


class NotificationDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
