"""Account email services — shared by signup, resend, the beat queue and admin."""

from __future__ import annotations

from django.core.cache import cache
from django.db import transaction

from apps.core.audit import record_audit
from apps.core.email import send_mail_async
from apps.core.logging import ctx, get_logger
from apps.core.services import ServiceError

from .tokens import frontend_link, make_email_token

log = get_logger("accounts")

# Cooldown so the periodic queue never re-emails the same user too often
# (manual "resend" ignores this; only the beat sweep respects it). Cache key is
# tenant-scoped automatically (apps.core.cache.tenant_key_func).
VERIFY_COOLDOWN_SECONDS = 6 * 60 * 60


def verify_cooldown_key(user_pk: int) -> str:
    return f"verify_sent:{user_pk}"


def recently_sent(user_pk: int) -> bool:
    return cache.get(verify_cooldown_key(user_pk)) is not None


def send_verification_email(user, *, school_name: str, slug: str | None) -> None:
    """Queue a verification email for one (unverified) user."""
    link = frontend_link(slug, "/verify-email", token=make_email_token(user.pk))
    send_mail_async(
        to_email=user.email,
        subject=f"Verify your email for {school_name} on YukiCares",
        body=(
            f"Confirm your email to activate your {school_name} account:\n\n{link}\n\n"
            "This link expires in 3 days."
        ),
        html_body=(
            f"<p>Confirm your email to activate your {school_name} account.</p>"
            f'<p><a href="{link}">Verify my email</a> (expires in 3 days).</p>'
        ),
    )
    cache.set(verify_cooldown_key(user.pk), 1, timeout=VERIFY_COOLDOWN_SECONDS)
    log.info(
        "verification email queued",
        **ctx(user=user.id, entity=slug, action="send_verification"),
    )


@transaction.atomic
def create_staff(*, email, first_name, last_name, role, password, actor=None):
    """
    Add a staff member to the current school (tenant schema). The admin sets an
    initial password; the user can change it later via forgot-password. Created
    users are email-verified (an admin vouches for them).
    """
    from .models import User

    email = email.strip().lower()
    if User.objects.filter(username__iexact=email).exists():
        raise ServiceError("A user with this email already exists.")

    user = User(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        email_verified=True,
    )
    user.set_password(password)
    user.save()

    log.info(
        "staff created email=%s role=%s",
        email,
        role,
        **ctx(user=getattr(actor, "id", "-"), entity=user.id, action="create_staff"),
    )
    record_audit(
        action="staff.created",
        entity=user,
        summary=f"Added {user.get_full_name() or email} as {role}",
        actor=actor,
    )
    return user
