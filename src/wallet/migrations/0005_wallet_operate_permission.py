# Generated by Django 3.1.1 on 2020-11-09 15:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0004_transaction_add_related_object'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wallet',
            options={'permissions': [('operate', 'permission to deposit/withdraw')]},
        ),
    ]
