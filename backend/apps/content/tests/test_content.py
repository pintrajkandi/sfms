"""Public blog & FAQ API — only published content is served."""

import pytest
from rest_framework.test import APIRequestFactory

from apps.content.models import FAQ, BlogPost
from apps.content.views import BlogPostDetail, BlogPostList, FAQList

pytestmark = [pytest.mark.django_db]


def test_blog_list_only_published():
    BlogPost.objects.create(title="Live post", body="hi", is_published=True)
    BlogPost.objects.create(title="Draft post", body="wip", is_published=False)

    resp = BlogPostList.as_view()(APIRequestFactory().get("/content/posts/"))
    titles = {row["title"] for row in resp.data}
    assert "Live post" in titles
    assert "Draft post" not in titles


def test_blog_slug_autofilled_and_publish_stamped():
    post = BlogPost.objects.create(title="Hello World", body="x", is_published=True)
    assert post.slug == "hello-world"
    assert post.published_at is not None  # stamped on first publish


def test_blog_detail_hides_unpublished():
    post = BlogPost.objects.create(title="Secret", body="x", is_published=False)
    view = BlogPostDetail.as_view()
    resp = view(APIRequestFactory().get(f"/content/posts/{post.slug}/"), slug=post.slug)
    assert resp.status_code == 404


def test_faq_list_only_published_and_ordered():
    FAQ.objects.create(question="B", answer="b", order=2, is_published=True)
    FAQ.objects.create(question="A", answer="a", order=1, is_published=True)
    FAQ.objects.create(question="Hidden", answer="h", order=0, is_published=False)

    resp = FAQList.as_view()(APIRequestFactory().get("/content/faqs/"))
    questions = [row["question"] for row in resp.data]
    assert questions == ["A", "B"]  # published only, ordered by `order`
