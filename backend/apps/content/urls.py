from django.urls import path

from .views import BlogPostDetail, BlogPostList, FAQList

urlpatterns = [
    path("posts/", BlogPostList.as_view(), name="content-posts"),
    path("posts/<slug:slug>/", BlogPostDetail.as_view(), name="content-post-detail"),
    path("faqs/", FAQList.as_view(), name="content-faqs"),
]
