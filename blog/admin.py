from django.contrib import admin
from .models import Post, Category, Tags, Comment


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'user', 'category', 'status')


class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_on')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tags, TagsAdmin)
admin.site.register(Comment, CommentAdmin)
