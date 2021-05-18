import datetime
from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _


ROLE_CHOICE = (
    ('Admin', _('Admin')),
    ('User', _('User')),
)

STATUS_CHOICE = (
    ('Drafted', _('Drafted')),
    ('Published', _('Published')),
    ('Rejected', _('Rejected')),
    ('Trashed', _('Trashed')),
)


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=STATUS_CHOICE)

    class Meta:
        ordering = ['-id']


class Category(models.Model):
    name = models.CharField(_('name'), max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True, editable=False)

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def category_posts(self):
        return Post.objects.filter(category=self).count()


class Tags(models.Model):
    name = models.CharField(_('name'), max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True, editable=False)

    def save(self, *args, **kwargs):
        temp_slug = slugify(self.name)
        if self.id:
            tag = Tags.objects.get(pk=self.id)
            if tag.name != self.name:
                self.slug = create_tag_slug(temp_slug)
        else:
            self.slug = create_tag_slug(temp_slug)
        super(Tags, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')


def create_tag_slug(temp_slug):
    slug_count = 0
    while True:
        try:
            Tags.objects.get(slug=temp_slug)
            slug_count += 1
            temp_slug = temp_slug + '-' + str(slug_count)
        except ObjectDoesNotExist:
            return temp_slug


class Post(models.Model):
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True, editable=False)
    created_on = models.DateTimeField(_('created on'), auto_now_add=True)
    updated_on = models.DateField(_('updated on'), auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('User'))
    content = models.TextField(_('content'))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_('Category'))
    tags = models.ManyToManyField(Tags, related_name='rel_posts', verbose_name=_('Tags'))
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICE, default='Drafted')
    featured_image = models.ImageField(_('featured image'), upload_to='static/blog/uploads/%Y/%m/%d/', blank=True, null=True)

    class Meta:
        ordering = ['-updated_on']

    def save(self, *args, **kwargs):
        temp_slug = slugify(self.title)
        if self.id:
            blog_post = Post.objects.get(pk=self.id)
            if blog_post.title != self.title:
                self.slug = create_slug(temp_slug)
        else:
            self.slug = create_slug(temp_slug)

        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def create_activity(self, user, content):
        return PostHistory.objects.create(
            user=user, post=self, content=content
        )

    def create_activity_instance(self, user, content):
        return PostHistory(
            user=user, post=self, content=content
        )

    def remove_activity(self):
        self.history.all().delete()

    def store_old_slug(self, old_slug):
        query = Post_Slugs.objects.filter(blog=self, slug=old_slug).values_list("slug", flat=True)
        if not (query and old_slug != self.slug):
            old_slug, _ = Post_Slugs.objects.get_or_create(blog=self, slug=old_slug)
            old_slug.is_active = False
            old_slug.save()
        active_slug, _ = Post_Slugs.objects.get_or_create(blog=self, slug=self.slug)
        active_slug.is_active = True
        active_slug.save()


def create_slug(temp_slug):
    slug_count = 0
    while True:
        try:
            Post.objects.get(slug=temp_slug)
            slug_count += 1
            temp_slug = temp_slug + '-' + str(slug_count)
        except ObjectDoesNotExist:
            return temp_slug


class Post_Slugs(models.Model):
    blog = models.ForeignKey(Post, related_name='slugs', on_delete=models.CASCADE, verbose_name=_('Post'))
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(_('is active?'), default=False)

    def __str__(self):
        return self.slug


class PostHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('User'))
    post = models.ForeignKey(Post, related_name='history', on_delete=models.CASCADE, verbose_name=_('Post'))
    content = models.CharField(_('content'), max_length=200)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    def __str__(self):
        return '{username} {content} {blog_title}'.format(
            username=str(self.user.get_username()),
            content=str(self.content),
            blog_title=str(self.post.title)
        )


class Image_File(models.Model):
    upload = models.FileField(_('upload'), upload_to="media/uploads/%Y/%m/%d/")
    date_created = models.DateTimeField(_('date created'), default=datetime.datetime.now)
    is_image = models.BooleanField(_('is image?'), default=True)
    thumbnail = models.FileField(_('thumbnail'), upload_to="media/uploads/%Y/%m/%d/", blank=True, null=True)

    def __str__(self):
        return self.date_created


class Comment(models.Model):
    slug = models.CharField(max_length=100, unique=True, editable=False)
    created_on = models.DateTimeField(_('created on'), auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('User'))
    content = models.TextField(_('content'))

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        temp_slug = slugify(self.content[0:30])
        if self.id:
            comment_post = Comment.objects.get(pk=self.id)
            if comment_post.title != self.content:
                self.slug = create_slug(temp_slug)
        else:
            self.slug = create_slug(temp_slug)

        super(Comment, self).save(*args, **kwargs)

