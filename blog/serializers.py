from rest_framework import serializers

from .models import BlogMedia, BlogPost, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class BlogMediaSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField()

    class Meta:
        model = BlogMedia
        fields = [
            'id', 'media_type', 'url', 'video_url', 'embed_html',
            'file_name', 'mime_type', 'width', 'height',
            'alt_text', 'caption', 'duration_seconds', 'order', 'created_at',
        ]


class BlogPostListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author.full_name', default='', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'post_type', 'category', 'excerpt',
            'cover_image_url', 'author_name', 'tags', 'is_featured',
            'view_count', 'like_count', 'published_at', 'created_at',
        ]

    def get_cover_image_url(self, obj):
        from utils.storage import media_url
        return media_url(obj.cover_image)


class BlogPostDetailSerializer(BlogPostListSerializer):
    media = BlogMediaSerializer(many=True, read_only=True)
    content_html = serializers.ReadOnlyField()

    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + [
            'content', 'content_html', 'media', 'meta_title', 'meta_description',
            'is_published',
        ]


class BlogPostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True,
    )

    class Meta:
        model = BlogPost
        fields = [
            'title', 'content', 'excerpt', 'category', 'cover_image',
            'meta_title', 'meta_description', 'is_featured', 'tags',
            'is_published',
        ]

    def _apply_tags(self, post, tag_names):
        tags = [Tag.objects.get_or_create(name=n.strip())[0] for n in tag_names if n.strip()]
        post.tags.set(tags)

    def create(self, validated_data):
        tag_names = validated_data.pop('tags', [])
        post = BlogPost.objects.create(**validated_data)
        if tag_names:
            self._apply_tags(post, tag_names)
        return post

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tags', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if tag_names is not None:
            self._apply_tags(instance, tag_names)
        return instance
