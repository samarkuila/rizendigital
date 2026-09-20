from django.db import migrations

OLD = ('Rizen Digital is a Kolkata digital marketing company for SEO, social media, PPC and web development. '
       'Get a free consultation and a clear growth plan.')
NEW = ('Rizen Digital is a digital marketing agency in Kolkata offering SEO, social media, PPC and web development. '
       'Get a free consultation and a clear growth plan.')


def forwards(apps, schema_editor):
    """SEO audit: the home meta description lacked the page's main keyword ("digital marketing agency in Kolkata").
    Only touches the row if it still has the original text, so a description edited in Studio is never overwritten."""
    Page = apps.get_model('home', 'Page')
    Page.objects.filter(page_tag='home', page_meta_description=OLD).update(page_meta_description=NEW)


def backwards(apps, schema_editor):
    Page = apps.get_model('home', 'Page')
    Page.objects.filter(page_tag='home', page_meta_description=NEW).update(page_meta_description=OLD)


class Migration(migrations.Migration):
    dependencies = [('home', '0006_seo_fields')]
    operations = [migrations.RunPython(forwards, backwards)]
