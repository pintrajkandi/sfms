"""Public, read-only endpoints for blog posts & FAQs (no auth, no tenant)."""

from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import FAQ, BlogPost
from .serializers import BlogPostDetailSerializer, BlogPostListSerializer, FAQSerializer


class BlogPostList(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    pagination_class = None
    serializer_class = BlogPostListSerializer

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)


class BlogPostDetail(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = BlogPostDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)


class FAQList(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    pagination_class = None
    serializer_class = FAQSerializer

    def get_queryset(self):
        return FAQ.objects.filter(is_published=True)
