import uuid

import bleach
import markdown as md
from django.conf import settings
from django.db import models
from django.utils.text import slugify

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'blockquote',
    'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'img', 'table', 'thead', 'tbody',
    'tr', 'th', 'td', 'hr',
]
ALLOWED_ATTRS = {'a': ['href', 'title', 'rel'], 'img': ['src', 'alt', 'title']}


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_tags'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    class PostType(models.TextChoices):
        TEXT = 'text', 'Text Only'
        TEXT_IMAGE = 'text_image', 'Text + Image'
        TEXT_VIDEO = 'text_video', 'Text + Video'
        TEXT_IMAGE_VIDEO = 'text_image_video', 'Text + Image + Video'
        IMAGE = 'image', 'Image Only'
        VIDEO = 'video', 'Video Only'

    class Category(models.TextChoices):
        LAW_ENFORCEMENT = 'law_enforcement', 'Law Enforcement'
        TECHNOLOGY = 'technology', 'Technology'
        AI = 'ai', 'Artificial Intelligence'
        LEGAL_UPDATES = 'legal_updates', 'Legal Updates'
        TRAINING = 'training', 'Training & Education'
        POLICY = 'policy', 'Policy & Procedure'
        GENERAL = 'general', 'General'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, blank=True)
    slug = models.SlugField(max_length=550, unique=True, blank=True)
    post_type = models.CharField(max_length=30, choices=PostType.choices, default=PostType.TEXT)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)

    content = models.TextField(blank=True)            # markdown source
    content_html = models.TextField(blank=True)       # rendered + sanitized
    excerpt = models.TextField(blank=True, max_length=500)
    cover_image = models.CharField(max_length=500, blank=True)  # storage key

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='blog_posts',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_posts'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['is_published', 'published_at']),
            models.Index(fields=['category']),
            models.Index(fields=['post_type']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base = slugify(self.title)
            self.slug = base
            i = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base}-{i}'
                i += 1
        if not self.slug:
            self.slug = str(self.id)

        if self.content:
            rendered = md.markdown(self.content, extensions=['fenced_code', 'tables', 'nl2br'])
            self.content_html = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

        super().save(*args, **kwargs)

    def recalc_post_type(self):
        """Auto-detect post_type from attached media + text."""
        has_images = self.media.filter(media_type='image').exists()
        has_videos = self.media.filter(media_type__in=['video', 'video_url']).exists()
        has_text = bool(self.content.strip())
        if has_text and has_images and has_videos:
            t = self.PostType.TEXT_IMAGE_VIDEO
        elif has_text and has_images:
            t = self.PostType.TEXT_IMAGE
        elif has_text and has_videos:
            t = self.PostType.TEXT_VIDEO
        elif has_images and has_videos:
            t = self.PostType.TEXT_IMAGE_VIDEO
        elif has_images:
            t = self.PostType.IMAGE
        elif has_videos:
            t = self.PostType.VIDEO
        else:
            t = self.PostType.TEXT
        if t != self.post_type:
            self.post_type = t
            super().save(update_fields=['post_type'])

    def __str__(self):
        return self.title or f'Post {self.id}'


class BlogMedia(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Uploaded Video'
        VIDEO_URL = 'video_url', 'Embedded Video URL'
        DOCUMENT = 'document', 'Document'

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=20, choices=MediaType.choices)

    s3_key = models.CharField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)

    video_url = models.URLField(blank=True)
    embed_html = models.TextField(blank=True)

    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    alt_text = models.CharField(max_length=300, blank=True)
    caption = models.CharField(max_length=500, blank=True)

    duration_seconds = models.PositiveIntegerField(default=0)
    thumbnail_s3_key = models.CharField(max_length=500, blank=True)

    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_media'
        ordering = ['order', 'created_at']

    @property
    def url(self):
        from utils.storage import media_url
        return media_url(self.s3_key)

    def __str__(self):
        return f'{self.media_type} for post {self.post_id}'
