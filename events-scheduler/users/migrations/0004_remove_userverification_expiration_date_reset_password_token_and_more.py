# Generated by Django 4.2.3 on 2023-07-22 17:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userverification',
            name='expiration_date_reset_password_token',
        ),
        migrations.RemoveField(
            model_name='userverification',
            name='token_reset_password',
        ),
    ]
