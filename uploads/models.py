from django.db import models
from django.contrib.auth.models import User
from accounts.models import Profile, DataTags
from django.conf import settings
from django.utils import timezone
import os
import hashlib
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
from PIL import Image
import moviepy.editor as mp
import shutil

class NewUploadMultiple(models.Model):
    title = models.CharField(max_length=100, null=True)
    mini_caption = models.CharField(max_length=30, null=True)
    detail = models.CharField(max_length=30, null=True)
    detail_url = models.URLField(max_length=80, null=True)
    created_on =  models.DateTimeField(auto_now=True, null=True)
    uploaded_by = models.ForeignKey(User, related_name='author', null=True, on_delete=models.CASCADE)
    commentable = models.BooleanField(default=True)
    commercial = models.BooleanField(default=False)

    def __str__(self):
        return "%d: %s" %(self.id, self.title)

class SponsoredUploadMultiple(models.Model):
    sponsored_post = models.ForeignKey('NewUploadMultiple', related_name='sponsored_media', on_delete=models.CASCADE)
    detail = models.CharField(max_length=30, blank=True, null=True)
    created_on =  models.DateTimeField(auto_now=True)
    expire_on =  models.DateTimeField(null=True)
    level = models.IntegerField(default=1)
    uploaded_by = models.ForeignKey(User, related_name='admin_author', null=True, on_delete=models.SET_NULL)
    user_pref = models.ManyToManyField('accounts.DataTags', related_name='user_ads_engagement')

class AdsStatsDataa(models.Model):
    data_stat = models.CharField(max_length=200, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

def generate_media_path(self, filename):
    filename, ext = os.path.splitext(filename.lower())
    filename = "%s.%s" %(slugify(filename),timezone.now())
    hs_index = hashlib.md5(filename.encode())
    filename = "%s%s" %(hs_index.hexdigest(), ext)
    return "%s/%s" %(settings.UPLOAD_PATH, filename)

class ImageGalery(models.Model):
    caption = models.CharField(max_length=100,blank=True, null=True)
    image_inst = models.ForeignKey('NewUploadMultiple', related_name='media_list', on_delete=models.CASCADE)
    media_file = models.FileField(upload_to=generate_media_path, unique=False, null=True)
    file_type = models.CharField(max_length=7, null=True)

    def new_upload_save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            if self.file_type == 'image':
                img = Image.open(self.media_file.path)
                if img.height > 2000 or img.width > 2000:
                    output_size = (img.height/2, img.width/2)
                    img.thumbnail(output_size)
                    img.save(self.media_file.path)
                    print('Conversion Succesful')
            if self.file_type == 'video':
                media_path, media_name = os.path.split(self.media_file.path)
                temp_folder_name = 'temp'
                temp_path = os.path.join(media_path, temp_folder_name)
                if not os.path.exists(temp_path):
                    os.mkdir(temp_path)
                shutil.move(self.media_file.path, temp_path)
                temp_media_path = os.path.join(temp_path, media_name)
                clip = mp.VideoFileClip(temp_media_path)
                if clip.duration > 121.0:
                    clip = clip.subclip(0,120)
                if clip.h > 360 or clip.w > 640:
                    clip.resize(height=360)
                clip.to_videofile(self.media_file.path)
                os.remove(temp_media_path)
                print('Conversion Succesful')
        except:
            print('Something went wrong')

class LikeImage(models.Model):
    image_inst = models.ForeignKey('NewUploadMultiple', related_name='liked_list', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='liked_by', on_delete=models.CASCADE, null=True)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s: %s" %(self.user, self.image_inst)

    # def __

class ImageComment(models.Model):
    image_inst = models.ForeignKey('NewUploadMultiple', related_name='comment_list', on_delete=models.CASCADE)
    comment = models.CharField(max_length=50, null=True)
    comment_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commenter', null=True)
    created_on = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return "%s: %s" %(self.comment_by.username, self.comment)

class LikeComment(models.Model):
    comment_inst = models.ForeignKey('ImageComment', related_name='liked_ins', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='comment_liked_by', on_delete=models.CASCADE, null=True)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s: %s" %(self.user, self.comment_inst)

class AllianceList(models.Model):
    pilot = models.ForeignKey(User, related_name='sherpherd', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='sheep', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)
    # profile_page = models.ForeignKey('Profile', null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "%s is following %s" %(self.following, self.pilot)

class BlockedUser(models.Model):
    pilot = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name='blocked', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s blocked %s" %(self.pilot, self.blocked)

class CollectionName(models.Model):
    pilot = models.ForeignKey(User, related_name='colection_name_by', on_delete=models.CASCADE)
    collection = models.CharField(max_length=30)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s is owned by %s" %(self.collection, self.pilot)

class SavedMedia(models.Model):
    saved_item = models.ForeignKey('NewUploadMultiple', related_name='saved_media', on_delete=models.CASCADE)
    users_instance = models.ForeignKey(User, related_name='user_insta', on_delete=models.CASCADE)
    collection_name = models.ForeignKey('CollectionName', null=True, related_name='collection_r_name', on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s was saved by %s" %(self.saved_item.title, self.users_instance.username)

class TaggedUser(models.Model):
    added_media = models.ForeignKey('NewUploadMultiple', related_name='taggable_media', on_delete=models.CASCADE)
    users_instance = models.ForeignKey(User, related_name='user_tbt', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s was taged to %s" %(self.users_instance.username, self.added_media.title)

class StatusMedia(models.Model):
    title = models.CharField(max_length=100, null=True)
    created_on =  models.DateTimeField(auto_now=True, null=True)
    uploaded_by = models.ForeignKey(User, related_name='author_status', null=True, on_delete=models.CASCADE)
    visibility = models.BooleanField(default=True)

    def __str__(self):
        return "%d: %s" %(self.id, self.title)

class StatusMediaGallery(models.Model):
    image_inst = models.ForeignKey('StatusMedia', on_delete=models.CASCADE)
    media_file = models.FileField(upload_to=generate_media_path)
    file_type = models.CharField(max_length=7, null=True)