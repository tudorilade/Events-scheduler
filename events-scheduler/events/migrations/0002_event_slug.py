# Generated by Django 4.2.3 on 2023-07-21 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='slug',
            field=models.SlugField(default='blabla', unique=True),
            preserve_default=False,
        ),
    ]
