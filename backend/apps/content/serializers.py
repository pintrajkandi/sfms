from rest_framework import serializers

from .models import FAQ, BlogPost


class BlogPostListSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ("id", "title", "slug", "excerpt", "author", "cover_image", "published_at")

    def get_cover_image(self, obj) -> str:
        return obj.cover_image.url if obj.cover_image else ""


class BlogPostDetailSerializer(BlogPostListSerializer):
    class Meta(BlogPostListSerializer.Meta):
        fields = (*BlogPostListSerializer.Meta.fields, "body")


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "category", "order")
