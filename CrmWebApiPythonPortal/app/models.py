"""
Definition of models.
"""

from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save

class CustomerLogin:
   username = models.CharField(max_length=50)
   password = models.CharField(max_length=50)

class UserProfile(models.Model):
    user = models.OneToOneField(User,parent_link=True,primary_key=True)
    crmid = models.CharField(max_length=36)

    def user_post_save(sender, instance, created, **kwargs):
        if created == True:
            p = UserProfile()
            p.user = instance
            p.save()

    post_save.connect(user_post_save, sender=User)