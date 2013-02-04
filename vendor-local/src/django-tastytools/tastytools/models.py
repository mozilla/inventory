from django.db import models

class Test(models.Model):
    text = models.CharField(default="", max_length=100)