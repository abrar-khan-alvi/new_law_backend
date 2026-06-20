from django_filters import rest_framework as filters

from .models import BlogPost


class BlogPostFilter(filters.FilterSet):
    tag = filters.CharFilter(field_name='tags__slug', lookup_expr='iexact')
    category = filters.CharFilter(field_name='category', lookup_expr='iexact')
    post_type = filters.CharFilter(field_name='post_type', lookup_expr='iexact')
    featured = filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model = BlogPost
        fields = ['tag', 'category', 'post_type', 'featured']
