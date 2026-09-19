"""Forms used by Rizen Studio editors."""
import re

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.text import slugify

from home.models import BlogPost, CaseStudy, LocationFAQ, LocationPage, Page, Service, SubService, Testimonial

from .bulk import RESERVED_TAGS
from .models import SiteSettings
from .utils import has_template_tags, validate_image

_DT = '%Y-%m-%dT%H:%M'

# shared widgets for the Rank-Math-style SEO fields
SEO_WIDGETS = {
    'seo_score': forms.HiddenInput(),
    'og_description': forms.Textarea(attrs={'rows': 2}),
    'og_image': forms.ClearableFileInput(),
    'focus_keyword': forms.TextInput(attrs={'placeholder': 'e.g. seo services kolkata', 'autocomplete': 'off', 'maxlength': 120}),
    'seo_canonical': forms.URLInput(attrs={'placeholder': 'https://… (leave empty to use this page)'}),
}
_TAG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class StudioForm(forms.ModelForm):
    """Adds the Studio CSS classes and safe image validation to every editor form."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            w = f.widget
            cls = w.attrs.get('class', '')
            if isinstance(w, forms.CheckboxInput):
                add = 'st-switch-input'
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                add = 'st-select'
            elif isinstance(w, forms.Textarea):
                add = 'st-textarea'
            elif isinstance(w, forms.FileInput):
                add = 'st-file'
            else:
                add = 'st-input'
            w.attrs['class'] = (cls + ' ' + add).strip()

    def clean(self):
        data = super().clean()
        for name, value in list(data.items()):
            if isinstance(value, UploadedFile):
                try:
                    validate_image(value)
                except forms.ValidationError as exc:
                    self.add_error(name, exc)
        score = data.get('seo_score')
        if score is not None:
            data['seo_score'] = max(0, min(100, int(score)))
        return data


def _unique_slug(model, base, exclude_pk=None, field='slug'):
    base = slugify(base)[:150] or 'item'
    slug, n = base, 2
    while model.objects.filter(**{field: slug}).exclude(pk=exclude_pk).exists():
        slug = '%s-%d' % (base, n)
        n += 1
    return slug


class PageForm(StudioForm):
    class Meta:
        model = Page
        fields = ['post_type', 'page_name', 'page_tag', 'page_meta_title', 'page_meta_keyword', 'page_meta_description',
                  'page_short_content', 'page_content', 'image', 'image_alt', 'image_title', 'schema_tag_text', 'focus_keyword', 'seo_score', 'seo_noindex', 'seo_canonical', 'og_title', 'og_description', 'og_image']
        widgets = {
            **SEO_WIDGETS,
            'page_meta_description': forms.Textarea(attrs={'rows': 3}),
            'page_meta_keyword': forms.Textarea(attrs={'rows': 2}),
            'page_short_content': forms.Textarea(attrs={'rows': 3}),
            'page_content': forms.Textarea(attrs={'rows': 18, 'data-editor': 'rich'}),
            'schema_tag_text': forms.Textarea(attrs={'rows': 6, 'class': 'st-mono', 'spellcheck': 'false'}),
            'image': forms.ClearableFileInput(),
        }
        labels = {'page_name': 'Page name', 'page_tag': 'URL slug', 'page_meta_title': 'Meta title',
                  'page_meta_keyword': 'Meta keywords', 'page_meta_description': 'Meta description',
                  'page_short_content': 'Short summary', 'page_content': 'Page content', 'image': 'Featured image',
                  'schema_tag_text': 'Custom structured data (JSON-LD <script> tag)'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['page_meta_keyword'].required = False
        self.fields['page_tag'].required = False
        self.fields['page_tag'].help_text = 'The address of the page, e.g. seo-services. Lowercase letters, numbers and hyphens.'
        self.is_home = bool(self.instance.pk and self.instance.page_tag == 'home')

    def clean_page_tag(self):
        tag = (self.cleaned_data.get('page_tag') or '').strip().strip('/').lower()
        if not tag:
            tag = slugify(self.data.get('page_name', ''))
        if self.instance.pk and tag == self.instance.page_tag:
            return tag
        if not _TAG_RE.match(tag):
            raise forms.ValidationError('Use lowercase letters, numbers and single hyphens only, e.g. seo-services.')
        if tag in RESERVED_TAGS:
            raise forms.ValidationError('"%s" is reserved by the site.' % tag)
        return tag

    def clean_page_content(self):
        content = self.cleaned_data.get('page_content', '')
        old = self.instance.page_content if self.instance.pk else ''
        if has_template_tags(content) and not has_template_tags(old):
            raise forms.ValidationError('Template tags ({% ... %}) are not allowed in new content.')
        return content

    def clean(self):
        data = super().clean()
        if not data.get('page_meta_keyword'):
            data['page_meta_keyword'] = data.get('page_name', '')
        return data


class BlogForm(StudioForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'slug', 'excerpt', 'content', 'meta_title', 'meta_description', 'featured_image', 'author', 'published_at', 'is_published', 'focus_keyword', 'seo_score', 'seo_noindex', 'seo_canonical', 'og_title', 'og_description', 'og_image']
        widgets = {
            **SEO_WIDGETS,
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 22, 'data-editor': 'rich'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=_DT),
            'featured_image': forms.ClearableFileInput(),
        }
        labels = {'featured_image': 'Featured image', 'is_published': 'Published'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['slug'].required = False
        self.fields['published_at'].input_formats = [_DT, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']

    def clean_slug(self):
        raw = self.cleaned_data.get('slug')
        if raw:
            return slugify(raw)
        return _unique_slug(BlogPost, self.data.get('title', ''), self.instance.pk)

    def clean(self):
        data = super().clean()
        if data.get('is_published') and not data.get('published_at'):
            data['published_at'] = timezone.now()
        return data


class LocationForm(StudioForm):
    class Meta:
        model = LocationPage
        fields = ['service', 'city', 'country', 'slug', 'headline', 'introduction', 'content', 'meta_title', 'meta_description',
                  'map_embed_url', 'latitude', 'longitude', 'is_published', 'focus_keyword', 'seo_score', 'seo_noindex', 'seo_canonical', 'og_title', 'og_description', 'og_image']
        widgets = {
            **SEO_WIDGETS,
            'introduction': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 16, 'data-editor': 'rich'}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {'is_published': 'Published', 'map_embed_url': 'Google Maps embed URL'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['slug'].required = False

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get('slug') or '')
        if not slug:
            svc = self.cleaned_data.get('service')
            slug = _unique_slug(LocationPage, '%s-%s' % (svc.name if svc else 'location', self.data.get('city', '')), self.instance.pk)
        return slug


class LocationFAQForm(forms.ModelForm):
    class Meta:
        model = LocationFAQ
        fields = ['question', 'answer', 'order']
        widgets = {'answer': forms.Textarea(attrs={'rows': 3}), 'order': forms.HiddenInput()}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['order'].required = False
        for n, f in self.fields.items():
            if n != 'order':
                f.widget.attrs['class'] = 'st-textarea' if isinstance(f.widget, forms.Textarea) else 'st-input'


LocationFAQFormSet = inlineformset_factory(LocationPage, LocationFAQ, form=LocationFAQForm, extra=0, can_delete=True)


class CaseForm(StudioForm):
    class Meta:
        model = CaseStudy
        fields = ['client_name', 'slug', 'industry', 'service', 'summary', 'challenge', 'solution', 'results',
                  'metric_1_value', 'metric_1_label', 'metric_2_value', 'metric_2_label', 'metric_3_value', 'metric_3_label',
                  'testimonial', 'testimonial_author', 'featured_image', 'meta_title', 'meta_description', 'published_at', 'is_published', 'focus_keyword', 'seo_score', 'seo_noindex', 'seo_canonical', 'og_title', 'og_description', 'og_image']
        widgets = {
            **SEO_WIDGETS,
            'summary': forms.Textarea(attrs={'rows': 2}),
            'challenge': forms.Textarea(attrs={'rows': 5}), 'solution': forms.Textarea(attrs={'rows': 5}), 'results': forms.Textarea(attrs={'rows': 5}),
            'testimonial': forms.Textarea(attrs={'rows': 3}), 'meta_description': forms.Textarea(attrs={'rows': 3}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=_DT),
            'featured_image': forms.ClearableFileInput(),
        }
        labels = {'is_published': 'Published', 'featured_image': 'Featured image'}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['slug'].required = False
        self.fields['published_at'].input_formats = [_DT, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get('slug') or '')
        return slug or _unique_slug(CaseStudy, self.data.get('client_name', ''), self.instance.pk)

    def clean(self):
        data = super().clean()
        if data.get('is_published') and not data.get('published_at'):
            data['published_at'] = timezone.now()
        return data


class TestimonialForm(StudioForm):
    class Meta:
        model = Testimonial
        fields = ['client_name', 'role', 'company_name', 'quote', 'photo', 'order', 'is_published']
        widgets = {'quote': forms.Textarea(attrs={'rows': 4}), 'photo': forms.ClearableFileInput()}
        labels = {'is_published': 'Published'}


class ServiceForm(StudioForm):
    class Meta:
        model = Service
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


class SubServiceForm(StudioForm):
    class Meta:
        model = SubService
        fields = ['service', 'name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


class SiteSettingsForm(StudioForm):
    class Meta:
        model = SiteSettings
        fields = ['phone', 'email', 'address', 'facebook', 'twitter', 'youtube', 'instagram', 'linkedin']
        labels = {'twitter': 'X / Twitter'}


FORMS = {
    'pages': PageForm, 'blog': BlogForm, 'locations': LocationForm, 'cases': CaseForm,
    'testimonials': TestimonialForm, 'services': ServiceForm, 'subservices': SubServiceForm,
}


# (card title, fields, in_sidebar) for each editor
FORM_GROUPS = {
    'pages': [
        ('Content', ['page_name', 'page_tag', 'page_short_content', 'page_content'], False),
        ('Page type', ['post_type'], True),
        ('Featured image', ['image', 'image_alt', 'image_title'], True),
        ('Advanced', ['schema_tag_text'], True),
    ],
    'blog': [
        ('Article', ['title', 'excerpt', 'content'], False),
        ('Publish', ['is_published', 'published_at', 'author'], True),
        ('Featured image', ['featured_image'], True),
    ],
    'locations': [
        ('Page content', ['headline', 'introduction', 'content'], False),
        ('Publish', ['is_published'], True),
        ('Target', ['service', 'city', 'country'], True),
        ('Map', ['map_embed_url', 'latitude', 'longitude'], True),
    ],
    'cases': [
        ('The story', ['client_name', 'summary', 'challenge', 'solution', 'results'], False),
        ('Headline metrics', ['metric_1_value', 'metric_1_label', 'metric_2_value', 'metric_2_label', 'metric_3_value', 'metric_3_label'], False),
        ('Client quote', ['testimonial', 'testimonial_author'], False),
        ('Publish', ['is_published', 'published_at'], True),
        ('Details', ['industry', 'service'], True),
        ('Featured image', ['featured_image'], True),
    ],
    'testimonials': [
        ('Quote', ['client_name', 'role', 'company_name', 'quote'], False),
        ('Publish', ['is_published', 'order'], True),
        ('Photo', ['photo'], True),
    ],
    'services': [('Service', ['name', 'description'], False)],
    'subservices': [('Sub-service', ['service', 'name', 'description'], False)],
}


# Rank-Math-style SEO panel: which fields feed the analyzer and which tabs hold which fields
SEO_PANELS = {
    'pages': {'general': ['page_meta_title', 'page_meta_description', 'page_meta_keyword'], 'title': 'page_name', 'seoTitle': 'page_meta_title',
              'desc': 'page_meta_description', 'slug': 'page_tag', 'content': ['page_content'], 'minWords': 300, 'prefix': '/'},
    'blog': {'general': ['slug', 'meta_title', 'meta_description'], 'title': 'title', 'seoTitle': 'meta_title',
             'desc': 'meta_description', 'slug': 'slug', 'content': ['content'], 'minWords': 600, 'prefix': '/blog/'},
    'locations': {'general': ['slug', 'meta_title', 'meta_description'], 'title': 'headline', 'seoTitle': 'meta_title',
                  'desc': 'meta_description', 'slug': 'slug', 'content': ['introduction', 'content'], 'minWords': 300, 'prefix': '/locations/'},
    'cases': {'general': ['slug', 'meta_title', 'meta_description'], 'title': 'client_name', 'seoTitle': 'meta_title',
              'desc': 'meta_description', 'slug': 'slug', 'content': ['summary', 'challenge', 'solution', 'results'], 'minWords': 300, 'prefix': '/case-studies/'},
}
SEO_SOCIAL = ['og_title', 'og_description', 'og_image']
SEO_ADVANCED = ['seo_canonical', 'seo_noindex']

