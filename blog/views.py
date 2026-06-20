import mimetypes
import re
import uuid

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from utils.pagination import StandardPagination
from utils.storage import delete_upload, store_upload

from .filters import BlogPostFilter
from .models import BlogMedia, BlogPost, Tag
from .serializers import (
    BlogMediaSerializer,
    BlogPostCreateSerializer,
    BlogPostDetailSerializer,
    BlogPostListSerializer,
    TagSerializer,
)

ALLOWED_IMAGE = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'}
ALLOWED_VIDEO = {'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'}


class BlogPostListView(APIView):
    """GET (public, published) / POST (admin) /api/blog/posts/"""

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == 'POST' else [AllowAny()]

    def get(self, request):
        qs = BlogPost.objects.filter(is_published=True).select_related(
            'author').prefetch_related('tags', 'media')
        qs = BlogPostFilter(request.GET, queryset=qs).qs
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        data = BlogPostListSerializer(page, many=True).data
        return paginator.get_paginated_response(data)

    def post(self, request):
        serializer = BlogPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        if str(request.data.get('publish', '')).lower() in ('true', '1'):
            post.is_published = True
            post.published_at = timezone.now()
            post.save(update_fields=['is_published', 'published_at'])
        return Response(BlogPostDetailSerializer(post).data, status=201)


class BlogPostDetailView(APIView):
    """GET (public) / PATCH / DELETE (admin) /api/blog/posts/<slug>/"""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdmin()]

    def get(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        BlogPost.objects.filter(pk=post.pk).update(view_count=post.view_count + 1)
        return Response(BlogPostDetailSerializer(post).data)

    def patch(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        serializer = BlogPostCreateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if 'publish' in request.data:
            publish = str(request.data.get('publish')).lower() in ('true', '1')
            post.is_published = publish
            post.published_at = timezone.now() if publish else None
            post.save(update_fields=['is_published', 'published_at'])
        return Response(BlogPostDetailSerializer(post).data)

    def delete(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        for m in post.media.all():
            delete_upload(m.s3_key)
        post.delete()
        return Response(status=204)


class BlogMediaUploadView(APIView):
    """POST /api/blog/posts/<slug>/media/ — admin uploads image/video or embeds a URL."""
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        media_type = request.data.get('media_type')

        # Embedded YouTube/Vimeo URL
        if media_type == 'video_url':
            video_url = request.data.get('video_url', '')
            if not video_url:
                return Response({'error': {'detail': 'video_url is required.'}}, status=400)
            media = BlogMedia.objects.create(
                post=post, media_type='video_url', video_url=video_url,
                embed_html=self._embed(video_url),
                caption=request.data.get('caption', ''),
                order=request.data.get('order', 0) or 0,
            )
            post.recalc_post_type()
            return Response(BlogMediaSerializer(media).data, status=201)

        # Uploaded file
        file = request.FILES.get('file')
        if not file:
            return Response({'error': {'detail': 'No file provided.'}}, status=400)

        mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        if media_type == 'image' and mime not in ALLOWED_IMAGE:
            return Response({'error': {'detail': f'Invalid image type: {mime}'}}, status=400)
        if media_type == 'video' and mime not in ALLOWED_VIDEO:
            return Response({'error': {'detail': f'Invalid video type: {mime}'}}, status=400)

        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else 'bin'
        key = f'blog/{media_type}s/{uuid.uuid4()}.{ext}'
        stored_key = store_upload(file, key, content_type=mime)

        media = BlogMedia.objects.create(
            post=post, media_type=media_type, s3_key=stored_key,
            file_name=file.name, file_size=file.size, mime_type=mime,
            alt_text=request.data.get('alt_text', ''),
            caption=request.data.get('caption', ''),
            order=request.data.get('order', 0) or 0,
        )
        post.recalc_post_type()
        return Response(BlogMediaSerializer(media).data, status=201)

    @staticmethod
    def _embed(url):
        yt = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})', url)
        if yt:
            return (f'<iframe width="560" height="315" '
                    f'src="https://www.youtube.com/embed/{yt.group(1)}" '
                    f'frameborder="0" allowfullscreen></iframe>')
        vm = re.search(r'vimeo\.com/(\d+)', url)
        if vm:
            return (f'<iframe src="https://player.vimeo.com/video/{vm.group(1)}" '
                    f'width="560" height="315" frameborder="0" allowfullscreen></iframe>')
        return f'<video src="{url}" controls></video>'


class BlogMediaDeleteView(APIView):
    """DELETE /api/blog/posts/<slug>/media/<media_id>/"""
    permission_classes = [IsAdmin]

    def delete(self, request, slug, media_id):
        post = get_object_or_404(BlogPost, slug=slug)
        media = get_object_or_404(BlogMedia, id=media_id, post=post)
        delete_upload(media.s3_key)
        if media.thumbnail_s3_key:
            delete_upload(media.thumbnail_s3_key)
        media.delete()
        post.recalc_post_type()
        return Response(status=204)


class TagListView(APIView):
    """GET /api/blog/tags/ — public."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(TagSerializer(Tag.objects.all(), many=True).data)
