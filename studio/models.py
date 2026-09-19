from django.core.cache import cache
from django.db import models

CACHE_KEY = 'studio_site_settings_v1'


class SiteSettings(models.Model):
    """Single-row store for public contact details, editable from Rizen Studio.

    Values left blank fall back to the environment settings (SITE_PHONE, SITE_*_URL).
    """
    phone = models.CharField(max_length=40, blank=True, help_text='Shown in the header, footer, contact page and structured data, e.g. +919812345678')
    email = models.EmailField(blank=True, help_text='Public contact email')
    address = models.CharField(max_length=250, blank=True, help_text='Public address line shown in the footer and contact page')
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True, verbose_name='X / Twitter')
    youtube = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site settings'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return 'Site settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(CACHE_KEY)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def as_dict(cls):
        """Cached values for the context processor (cheap on every request)."""
        data = cache.get(CACHE_KEY)
        if data is None:
            o = cls.load()
            data = {f: getattr(o, f) for f in ('phone', 'email', 'address', 'facebook', 'twitter', 'youtube', 'instagram', 'linkedin')}
            cache.set(CACHE_KEY, data, 60)
        return data
