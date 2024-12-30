# Generated by Django 5.1.2 on 2024-12-30 02:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('post_type', models.CharField(choices=[('Page', 'Page'), ('Blog', 'Blog'), ('Custom_Page', 'Custom_Page')], max_length=500)),
                ('page_name', models.CharField(max_length=500)),
                ('page_meta_title', models.CharField(max_length=80)),
                ('page_meta_keyword', models.TextField()),
                ('page_meta_description', models.TextField()),
                ('page_tag', models.CharField(blank=True, max_length=500, unique=True)),
                ('image', models.FileField(blank=True, upload_to='page/')),
                ('image_alt', models.CharField(blank=True, max_length=100)),
                ('image_title', models.CharField(blank=True, max_length=100)),
                ('page_short_content', models.TextField(blank=True, max_length=500, null=True)),
                ('page_content', models.TextField()),
                ('post_date_time', models.DateTimeField(auto_now_add=True)),
                ('schema_tag_text', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('page', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.page')),
            ],
        ),
        migrations.CreateModel(
            name='SubService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('page', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.page')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subservices', to='home.service')),
            ],
        ),
    ]
