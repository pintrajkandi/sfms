"""Verified WhatsApp support hand-off — code issuance + persistence."""

import pytest
from django.test import override_settings
from django_tenants.utils import schema_context

from apps.tenants.models import WhatsAppSupportCode
from apps.tenants.whatsapp_support import issue_whatsapp_code

pytestmark = [pytest.mark.django_db]


class _User:
    id = 1
    full_name = "Ada Lovelace"
    email = "ada@test.school"
    phone = "9876543210"
    username = "ada"


@override_settings(SUPPORT_WHATSAPP_NUMBER="919876543210")
def test_issue_code_builds_verifiable_link(tenant_ctx):
    data = issue_whatsapp_code(user=_User(), topic="Payment not recorded")

    assert data["code"].startswith("YC-")
    assert data["configured"] is True
    assert "wa.me/919876543210" in data["whatsapp_url"]
    assert data["code"] in data["whatsapp_url"]  # the code rides in the prefilled text

    # Persisted in the PUBLIC schema so the platform agent can verify any school.
    with schema_context("public"):
        obj = WhatsAppSupportCode.objects.get(code=data["code"])
        assert obj.schema_name == "test"
        assert obj.school_name == "Test School"
        assert obj.status == WhatsAppSupportCode.Status.ISSUED
        assert not obj.is_expired


@override_settings(SUPPORT_WHATSAPP_NUMBER="")
def test_unconfigured_number_returns_no_link(tenant_ctx):
    data = issue_whatsapp_code(user=_User())
    assert data["configured"] is False
    assert data["whatsapp_url"] == ""
    assert data["code"].startswith("YC-")  # code is still issued (email fallback)
