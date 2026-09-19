from django.db import models

class GetTouchWithUs(models.Model):
    SERVICE_CHOICES = [
        ('seo', 'Search Engine Optimization'),
        ('google_local', 'Google Local Listing'),
        ('adwords', 'Google Adwords'),
        ('web_design', 'Website Design & Development'),
        ('wordpress', 'WordPress Website'),
        ('ecommerce', 'eCommerce Website'),
        ('social_media', 'Social Media Marketing'),
        ('facebook_ads', 'Facebook Ads'),
        ('youtube_ads', 'YouTube Ads'),
        ('others', 'Others'),
    ]
    full_name = models.CharField(max_length=500)
    email = models.EmailField(max_length=500)
    phone_number = models.CharField(max_length=500)
    company_name = models.CharField(max_length=500, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True, default='')
    website_url = models.URLField(max_length=500, blank=True, null=True)
    select_service = models.CharField(max_length=500, choices=SERVICE_CHOICES, blank=True, null=True)
    added_date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Get in Touch"
        verbose_name_plural = "Get in Touch"

    def __str__(self):
        return self.full_name

