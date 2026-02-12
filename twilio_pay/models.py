from django.db import models
from django.utils import timezone
import random

class OTP(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def generate_otp(self):
        self.code = str(random.randint(100000, 999999))
        return self.code
