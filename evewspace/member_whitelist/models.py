from django.db import models

# Create your models here.

class WhitelistEntry(models.Model):
    """
    A name that the current users will be checked against.
    """
    entry = models.CharField(max_length=255, unique=True)
    
    class Meta:
        permissions = {("whitelist_exempt", "Exempt from whitelist checking.")}
