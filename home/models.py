import logging
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db import transaction, IntegrityError
from django.urls import reverse

logger = logging.getLogger(__name__)

# Define Post Types
POST_TYPES = (('Page', 'Page'), ('Blog', 'Blog'), ('Custom_Page', 'Custom_Page'))  # Example post types


class SeoFields(models.Model):
    """Rank-Math-style SEO settings shared by pages, posts, location pages and case studies."""
    focus_keyword = models.CharField(max_length=120, blank=True, help_text='The main phrase this page should rank for.')
    seo_score = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Last score from the Studio SEO analyzer (0-100).')
    seo_noindex = models.BooleanField(default=False, verbose_name='Hide from search engines', help_text='Adds noindex and removes the page from the sitemap.')
    seo_canonical = models.URLField(max_length=500, blank=True, verbose_name='Canonical URL', help_text='Only set this if the page duplicates another address.')
    og_title = models.CharField(max_length=120, blank=True, verbose_name='Social title')
    og_description = models.CharField(max_length=300, blank=True, verbose_name='Social description')
    og_image = models.FileField(upload_to='social/', blank=True, verbose_name='Social image')

    class Meta:
        abstract = True


# Page Model
class Page(SeoFields, models.Model):
    id = models.AutoField(primary_key=True)
    post_type = models.CharField(max_length=500, choices=POST_TYPES)
    page_name = models.CharField(max_length=500)
    page_meta_title = models.CharField(max_length=80)
    page_meta_keyword = models.TextField()
    page_meta_description = models.TextField()
    page_tag = models.CharField(max_length=500, blank=True, unique=True)  # Unique field
    image = models.FileField(upload_to='page/', blank=True)
    image_alt = models.CharField(max_length=100, blank=True)
    image_title = models.CharField(max_length=100, blank=True)
    page_short_content = models.TextField(max_length=500, blank=True, null=True)
    page_content = models.TextField()
    post_date_time = models.DateTimeField(auto_now_add=True)
    schema_tag_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.page_name


# Service Model
class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    page = models.OneToOneField(Page, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def _create_service_page(self):
        service_slug = slugify(self.name)
        try:
            page = Page.objects.create(
                post_type='Custom_Page',
                page_name=self.name,
                page_meta_title=self.name,
                page_meta_keyword=self.name,
                page_meta_description=self.description or '',
                page_tag=f"{service_slug}",
                page_content=self.description or '',
            )
            self.page = page
            self.save()
        except IntegrityError:
            raise ValueError(f"A Page with the tag '{service_slug}' already exists.")

    def save(self, *args, **kwargs):
        if not self.page and not self.pk:
            # _create_service_page() attaches the new Page and saves this service itself.
            self._create_service_page()
            return
        super(Service, self).save(*args, **kwargs)


@receiver(post_delete, sender=Service)
def delete_service_page(sender, instance, **kwargs):
    if instance.page:
        instance.page.delete()


# SubService Model
class SubService(models.Model):
    service = models.ForeignKey('Service', related_name='subservices', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    page = models.OneToOneField('Page', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def _create_subservice_page(self):
        service_name = slugify(self.service.name)
        page_slug = slugify(self.name)
        page_tag = f"{service_name}/{page_slug}"
        
        try:
            page, created = Page.objects.get_or_create(
                page_tag=page_tag,
                defaults={
                    'post_type': 'Custom_Page',
                    'page_name': self.name,
                    'page_meta_title': self.name,
                    'page_meta_keyword': self.name,
                    'page_meta_description': self.description or '',
                    'page_content': self.description or '',
                }
            )
            self.page = page
            self.save()
        except IntegrityError:
            raise ValueError(f"A Page with the tag '{page_tag}' already exists.")

    def save(self, *args, **kwargs):
        if not self.page and not self.pk:
            super(SubService, self).save(*args, **kwargs)  # Save first to get a PK
            self._create_subservice_page()
        else:
            super(SubService, self).save(*args, **kwargs)

    def get_slugs(self):
        if self.page and self.page.page_tag:
            try:
                service_slug, subservice_slug = self.page.page_tag.split('/')
                return service_slug, subservice_slug
            except ValueError:
                logger.warning(f"Invalid page_tag format: {self.page.page_tag}")
                return None, None
        return None, None

    def get_absolute_url(self):
        service_slug, subservice_slug = self.get_slugs()
        if service_slug and subservice_slug:
            return reverse('subservice_detail', kwargs={
                'service_slug': service_slug,
                'subservice_slug': subservice_slug
            })
        return '#'


class BlogPost(SeoFields, models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    featured_image = models.FileField(upload_to='blog/', blank=True)
    author = models.CharField(max_length=120, default='Rizen Digital')
    published_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog-detail', kwargs={'page_tag': self.slug})


class Testimonial(models.Model):
    client_name = models.CharField(max_length=120)
    role = models.CharField(max_length=150, blank=True, help_text='e.g. "Business Owner", "Marketing Director"')
    company_name = models.CharField(max_length=150, blank=True)
    quote = models.TextField(max_length=500)
    photo = models.FileField(upload_to='testimonials/', blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('order', '-created_at')

    def __str__(self):
        return f'{self.client_name} ({self.company_name})' if self.company_name else self.client_name


class CaseStudy(SeoFields, models.Model):
    client_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=200, unique=True)
    industry = models.CharField(max_length=120, blank=True)
    service = models.ForeignKey(
        Service, related_name='case_studies', on_delete=models.SET_NULL, null=True, blank=True
    )
    summary = models.TextField(
        max_length=500,
        help_text='One or two sentence result-focused summary, e.g. "Increased organic traffic by 52% in 6 months."',
    )
    challenge = models.TextField(help_text="What problem was the client facing?")
    solution = models.TextField(help_text="What did Rizen Digital do?")
    results = models.TextField(help_text="What outcome did the client get?")
    metric_1_value = models.CharField(max_length=20, blank=True, help_text='e.g. "52%"')
    metric_1_label = models.CharField(max_length=60, blank=True, help_text='e.g. "Organic traffic increase"')
    metric_2_value = models.CharField(max_length=20, blank=True)
    metric_2_label = models.CharField(max_length=60, blank=True)
    metric_3_value = models.CharField(max_length=20, blank=True)
    metric_3_label = models.CharField(max_length=60, blank=True)
    testimonial = models.TextField(blank=True)
    testimonial_author = models.CharField(max_length=120, blank=True)
    featured_image = models.FileField(upload_to='case-studies/', blank=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at')
        verbose_name = 'Case study'
        verbose_name_plural = 'Case studies'

    def __str__(self):
        return self.client_name

    def get_absolute_url(self):
        return reverse('case_study_detail', kwargs={'slug': self.slug})


class LocationPage(SeoFields, models.Model):
    service = models.ForeignKey(Service, related_name='location_pages', on_delete=models.CASCADE)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=160, unique=True)
    headline = models.CharField(max_length=180)
    introduction = models.TextField(max_length=700)
    content = models.TextField()
    meta_title = models.CharField(max_length=60)
    meta_description = models.CharField(max_length=160)
    map_embed_url = models.URLField(blank=True, help_text='Google Maps embed URL (src of an <iframe>).')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('city', 'service__name')
        verbose_name = 'Location service page'
        verbose_name_plural = 'Location service pages'

    def __str__(self):
        return f'{self.service.name} in {self.city}'

    def get_absolute_url(self):
        return reverse('location_detail', kwargs={'slug': self.slug})


class LocationFAQ(models.Model):
    location_page = models.ForeignKey(LocationPage, related_name='faqs', on_delete=models.CASCADE)
    question = models.CharField(max_length=200)
    answer = models.TextField(max_length=600)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order', 'id')
        verbose_name = 'Location FAQ'
        verbose_name_plural = 'Location FAQs'

    def __str__(self):
        return f'{self.question} ({self.location_page.city})'


# Global flag to prevent recursion during deletion
_deletion_in_progress = False


@receiver(pre_delete, sender=Service)
def delete_associated_page_service(sender, instance, **kwargs):
    global _deletion_in_progress
    if _deletion_in_progress:
        return

    _deletion_in_progress = True
    try:
        if instance.page:
            try:
                with transaction.atomic():
                    instance.page.delete()
            except models.ObjectDoesNotExist:
                pass
    finally:
        _deletion_in_progress = False


@receiver(post_delete, sender=Service)
def delete_related_subservices(sender, instance, **kwargs):
    global _deletion_in_progress
    if _deletion_in_progress:
        return

    _deletion_in_progress = True
    try:
        for subservice in instance.subservices.all():
            if subservice.page:
                try:
                    with transaction.atomic():
                        subservice.page.delete()
                except models.ObjectDoesNotExist:
                    pass
            subservice.delete()
    finally:
        _deletion_in_progress = False


@receiver(post_delete, sender=SubService)
def delete_associated_page_subservice(sender, instance, **kwargs):
    if instance.page:
        try:
            with transaction.atomic():
                instance.page.delete()
        except models.ObjectDoesNotExist:
            pass
