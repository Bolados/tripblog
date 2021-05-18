from django.shortcuts import render
from .models import Post, Comment, Category, Tags
from django.views.generic import ListView, DetailView


def index(request):
    return render(request, 'blog/index.html', {})


class PostListView(ListView):
    model = Post
    template_name = 'posts/list.html'
    context_object_name = 'blog_list'

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        context['latest_posts'] = self.model.objects.filter(status='Published')[:3]
        context['categories'] = Category.objects.all()
        context['tags'] = Tags.objects.all()
        return context


def post_detail(request, slug):
    post = Post.objects.get(slug=slug)
    context = {
        'latest_posts': Post.objects.filter(status='Published')[:3],
        'categories': Category.objects.all(),
        'tags': Tags.objects.all(),
        'post': post,
    }
    return render(request, 'posts/detail.html', context)
