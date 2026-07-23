from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.logging import ctx, get_logger

from .models import PushSubscription
from .push import push_broadcast, push_enabled

log = get_logger("notifications.push")


class VapidKeyView(APIView):
    """Public VAPID key + whether push is configured (for the subscribe flow)."""

    def get(self, request):
        return Response({"public_key": settings.VAPID_PUBLIC_KEY, "enabled": push_enabled()})


class PushSubscribeView(APIView):
    def post(self, request):
        sub = request.data.get("subscription") or request.data
        endpoint = sub.get("endpoint")
        keys = sub.get("keys", {})
        if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
            return Response({"detail": "Invalid subscription."}, status=400)
        user = request.user if request.user.is_authenticated else None
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={"p256dh": keys["p256dh"], "auth": keys["auth"], "user": user},
        )
        log.info("push subscribed", **ctx(user=getattr(user, "id", "-"), action="push_subscribe"))
        return Response({"status": "subscribed"}, status=201)


class PushUnsubscribeView(APIView):
    def post(self, request):
        endpoint = request.data.get("endpoint")
        if endpoint:
            PushSubscription.objects.filter(endpoint=endpoint).delete()
        return Response(status=204)


class PushTestView(APIView):
    """Send a test push to every subscription in this school."""

    def post(self, request):
        sent = push_broadcast("Fee Ledger", "🔔 Test notification — push is working.", url="/")
        return Response({"sent": sent})
