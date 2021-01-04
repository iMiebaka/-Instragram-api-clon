from django.db import models
# from uploads.models import DataTags
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
from .select_options import COUNTRY, sex 
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta, datetime
from PIL import Image
import hashlib
User = settings.AUTH_USER_MODEL

# Create your models here.
# def generate_media_path(self, request, filename):
def generate_media_path(self, filename):
    filename, ext = os.path.splitext(filename.lower())
    filename = "%s.%s" %(slugify(filename), timezone.now())
    # filename = "%s.%s.%s" %(slugify(filename), str(request.user), timezone.now())
    hs_index = hashlib.md5(filename.encode())
    filename = "%s%s" %(hs_index.hexdigest(), ext)
    return "%s/%s" %(settings.UPLOAD_PATH, filename)


class DataTags(models.Model):
    tags = models.CharField(max_length=20, null=True)

    def __str__(self):
        return str(self.tags)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    mobile = models.IntegerField(null=True, blank=False)
    profile_complete = models.BooleanField(null=True, default=False)
    display_last_seen = models.BooleanField(null=True, default=True)
    last_seen = models.DateTimeField(default=timezone.now, null=True)
    birth_date = models.DateField(null=True , blank=True)
    website = models.URLField(null=True)
    bio = models.TextField(max_length=200 , null=True, blank=True)
    sex = models.CharField(max_length=6, choices=sex, null=True, blank=True)
    location = models.CharField(max_length=20 , choices=COUNTRY, null=True, blank=True)
    cover_image = models.ImageField(default='default_image.jpg', null=True, upload_to=settings.UPLOAD_PATH_PROFILE) 
    isVerified = models.BooleanField(null=True, default=False)
    opt_email = models.BooleanField(default=True)
    otp_mobile = models.BooleanField(default=False)
    two_step_verification = models.BooleanField(null=True, default=False)
    counter = models.IntegerField(default=0, null=True)   # For HOTP Verification
    user_pref = models.ManyToManyField('DataTags', related_name='user_engagement')

    def __str__(self):
        return str(self.user)

    def last_seen_cache(self):
        return cache.get('seen_%s' %self.user.username)

    @property
    def last_seen_algorithm(self):
        if self.display_last_seen:
            ls = str(self.last_seen.date())
            now = str(timezone.now().date())
            if now == ls:
                return ('last seen today at %s' %self.last_seen.time())
            if now > ls:
                return ('last seen %s' %self.last_seen.date())
        else:
            return None

    @property
    def online(self):
        if self.display_last_seen:
            if self.last_seen_cache():
                now = timezone.now()
                if now > self.last_seen_cache() + timedelta(seconds=settings.USER_ONLINE_TIMEOUT):
                    return False
                else:
                    return True
            else:
                return False
        else:
            return None


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.cover_image.path)
        if img.height > 2000 or img.width > 2000:
            output_size = (img.height/2, img.width/2)
            img.thumbnail(output_size)
            img.save(self.cover_image.path)

class LoginLogsheet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Token.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
