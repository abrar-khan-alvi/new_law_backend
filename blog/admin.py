from django.contrib import admin

from .models import BlogMedia, BlogPost, Tag


class BlogMediaInline(admin.TabularInline):
    model = BlogMedia
    extra = 0


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'post_type', 'is_published', 'is_featured', 'published_at')
    list_filter = ('category', 'post_type', 'is_published', 'is_featured')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [BlogMediaInline]
    raw_id_fields = ('author',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


admin.site.register(BlogMedia)
