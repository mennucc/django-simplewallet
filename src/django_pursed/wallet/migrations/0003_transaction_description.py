# Generated by Django 3.1.1 on 2020-11-09 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0002_alter_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='description',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
