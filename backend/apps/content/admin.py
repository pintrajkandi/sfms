"""Blog & FAQ management — mounted on the platform (public) admin console."""

from unfold.admin import ModelAdmin

from apps.tenants.admin_site import platform_admin

from .models import FAQ, BlogPost


class BlogPostAdmin(ModelAdmin):
    list_display = ("title", "author", "is_published", "published_at", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "title",
        "slug",
        "author",
        "cover_image",
        "excerpt",
        "body",
        "is_published",
        "published_at",
        "created_at",
        "updated_at",
    )


class FAQAdmin(ModelAdmin):
    list_display = ("question", "category", "order", "is_published")
    list_filter = ("is_published", "category")
    search_fields = ("question", "answer")
    list_editable = ("order", "is_published")


platform_admin.register(BlogPost, BlogPostAdmin)
platform_admin.register(FAQ, FAQAdmin)
