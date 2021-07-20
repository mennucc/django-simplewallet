from django.conf import settings
from django.db import models



AUTH_USER_MODEL = settings.AUTH_USER_MODEL

class BuyableObject(models.Model):
    class Meta:
        app_label = 'toystore'
    #
    description = models.CharField(max_length=300, db_index = True, blank=True)
    #
    owners = models.ManyToManyField(AUTH_USER_MODEL)
