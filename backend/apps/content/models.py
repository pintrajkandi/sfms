"""Public marketing content — blog posts & FAQs (CLAUDE.md §3: shared schema).

These live in the PUBLIC schema (SHARED_APPS): they are global site content,
not per-school data. Managed from the platform admin, served read-only to the
public frontend.
"""

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Auto-filled from the title if left blank.",
    )
    excerpt = models.CharField(
        max_length=300, blank=True, help_text="Short summary shown on the blog list."
    )
    body = models.TextField(help_text="Post content. Separate paragraphs with a blank line.")
    cover_image = models.ImageField(upload_to="blog/", null=True, blank=True)
    author = models.CharField(max_length=120, blank=True)
    is_published = models.BooleanField(
        default=False, help_text="Only published posts appear on the site."
    )
    published_at = models.DateTimeField(
        null=True, blank=True, help_text="Set automatically when first published."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "post"
            slug = base
            n = 2
            while BlogPost.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        # Stamp the publish time the first time it goes live.
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(
        max_length=80, blank=True, help_text="Optional grouping, e.g. 'Billing'."
    )
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self) -> str:
        return self.question
