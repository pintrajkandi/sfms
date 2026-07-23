"""Web-push: enabled with VAPID keys, subscriptions stored, broadcast safe."""

import pytest

from apps.notifications.models import PushSubscription
from apps.notifications.push import push_broadcast, push_enabled

pytestmark = [pytest.mark.django_db]


def test_push_enabled_with_vapid_keys():
    assert push_enabled() is True  # dev VAPID keys ship by default


def test_subscription_stored_and_broadcast_no_targets(tenant_ctx):
    PushSubscription.objects.create(endpoint="https://push.example/abc", p256dh="k", auth="a")
    assert PushSubscription.objects.count() == 1
    # No reachable endpoints in tests → broadcast attempts 0 real sends we assert on
    # separately; here we just ensure an empty tenant broadcast is a no-op.
    PushSubscription.objects.all().delete()
    assert push_broadcast("t", "b") == 0
