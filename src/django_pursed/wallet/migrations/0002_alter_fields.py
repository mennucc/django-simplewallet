# Generated by Django 3.1.1 on 2020-11-09 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
