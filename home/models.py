from django.db import models
from django.utils.text import slugify
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db import transaction, IntegrityError
from django.urls import reverse

# Define Post Types
POST_TYPES = (('Page', 'Page'), ('Blog', 'Blog'), ('Custom_Page', 'Custom_Page'))  # Example post types


# Page Model
class Page(models.Model):
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
            self._create_service_page()
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
                print(f"Invalid page_tag format: {self.page.page_tag}")
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


# Global flag to prevent recursion during deletion
_deletion_in_progress = False


@receiver(pre_delete, sender=Service)
def delete_associated_page_service(sender, instance, **kwargs):
    global _deletion_in_progress
    if _deletion_in_progress:
        return

    _deletion_in_progress = True

    if instance.page:
        try:
            with transaction.atomic():
                instance.page.delete()
        except models.ObjectDoesNotExist:
            pass


@receiver(post_delete, sender=Service)
def delete_related_subservices(sender, instance, **kwargs):
    global _deletion_in_progress
    if _deletion_in_progress:
        return

    _deletion_in_progress = True

    for subservice in instance.subservices.all():
        if subservice.page:
            try:
                with transaction.atomic():
                    subservice.page.delete()
            except models.ObjectDoesNotExist:
                pass
        subservice.delete()

    _deletion_in_progress = False


@receiver(post_delete, sender=SubService)
def delete_associated_page_subservice(sender, instance, **kwargs):
    if instance.page:
        try:
            with transaction.atomic():
                instance.page.delete()
        except models.ObjectDoesNotExist:
            pass
