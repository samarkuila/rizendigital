"""Template helpers that keep the contact email out of the page source as plain text (scrapers read raw HTML).

Usage:
    <a {% mail_attrs site_email %}><i class="..."></i> <span class="js-mail-text">{{ site_email|mail_masked }}</span></a>
A small script in layout.html rebuilds the real mailto link and text in the browser.
"""
from django import template
from django.urls import reverse
from django.utils.html import format_html

register = template.Library()


@register.filter
def mail_masked(value):
    return (value or '').replace('@', ' [at] ')


@register.simple_tag
def mail_attrs(email):
    user, _, domain = (email or '').partition('@')
    return format_html('class="js-mail" href="{}" data-u="{}" data-d="{}" rel="nofollow"', reverse('contact'), user, domain)
