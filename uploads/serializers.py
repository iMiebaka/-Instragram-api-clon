from rest_framework import serializers
from .models import NewUploadMultiple, ImageGalery, SponsoredUploadMultiple, LikeImage, ImageComment, AllianceList, TaggedUser, SavedMedia, StatusMedia, LikeComment
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from accounts.models import Profile
from django.contrib.sites.shortcuts import get_current_site


class TaggedUserSerializer(serializers.ModelSerializer):
    tagged_to = serializers.SerializerMethodField('user_tag')

    def user_tag(self, obj):
        return obj.users_instance.username

    class Meta:
        model = TaggedUser
        fields = ['tagged_to']


class ImageGalerySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ImageGalery
        fields = ['id', 'caption', 'media_file', 'file_type']


class LikedImageSerializer(serializers.ModelSerializer):
    liked_by = serializers.SerializerMethodField('user')

    def user(self, obj):
        return obj.user.username

    class Meta:
        model = LikeImage
        fields = ['liked_by']


class LikedCommentSerializer(serializers.ModelSerializer):
    comment_liked_by_username = serializers.SerializerMethodField('user')
    comment_liked_by_fullname = serializers.SerializerMethodField('fullname')
    comment_liked_by_profile_picture = serializers.SerializerMethodField('get_profile_picture')
    status_available = serializers.SerializerMethodField('check_status')

    def user(self, obj):
        return obj.user.username

    def fullname(self, obj):
        return obj.user.first_name

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(Profile.objects.get(user=obj.user).cover_image.url)
    
    def check_status(self, obj):
        try:
            StatusMedia.objects.get(uploaded_by=obj.user, visibility=False)
            return True
        except StatusMedia.DoesNotExist:
            return False

    def follow_back_check(self, obj):
        request = self.context.get("request")
        try:
            AllianceList.objects.get(pilot=obj.user, following=request.user)
            return True
        except AllianceList.DoesNotExist:
            return False

    class Meta:
        model = LikeComment
        fields = ['comment_liked_by_username', 'comment_liked_by_fullname', 'comment_liked_by_profile_picture', 'status_available']


class ImageCommentSerializer(serializers.ModelSerializer):
    comment_by = serializers.SerializerMethodField('comment')
    comment_likes = serializers.SerializerMethodField('comment_like')
    status_available = serializers.SerializerMethodField('check_status')
    profile_picture = serializers.SerializerMethodField('get_profile_picture')

    def comment(self, obj):
        return obj.comment_by.username

    def comment_like(self, obj):
        cl = LikeComment.objects.filter(comment_inst=obj).count()
        return cl

    def check_status(self, obj):
        try:
            StatusMedia.objects.get(uploaded_by=obj.comment_by, visibility=False)
            return True
        except StatusMedia.DoesNotExist:
            return False

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        print(Profile.objects.get(user=obj.comment_by).cover_image.url)
        return None
        return request.build_absolute_uri(Profile.objects.get(user=obj.comment_by).cover_image.url)

    class Meta:
        model = ImageComment
        fields = ['id', 'comment_by', 'comment', 'created_on', 'comment_likes', 'status_available', 'profile_picture']


class ImageCommentSerializerMain(serializers.ModelSerializer):
    comment_by = serializers.SerializerMethodField('comment')
    comment_likes = serializers.SerializerMethodField('comment_like')
    status_available = serializers.SerializerMethodField('check_status')

    def comment(self, obj):
        return obj.comment_by.username

    def comment_like(self, obj):
        cl = LikeComment.objects.filter(comment_inst=obj).count()
        return cl

    def check_status(self, obj):
        try:
            StatusMedia.objects.get(uploaded_by=obj.comment_by, visibility=False)
            return True
        except StatusMedia.DoesNotExist:
            return False

    class Meta:
        model = ImageComment
        fields = ['id', 'comment_by', 'comment', 'created_on', 'comment_likes', 'status_available']


class NewUploadMultipleSerializer(serializers.ModelSerializer):
    media_list = ImageGalerySerializer(many=True, read_only=True)
    liked_list = serializers.SerializerMethodField('pagination_like')
    comment_list = serializers.SerializerMethodField('pagination_comment')
    tagged_list = serializers.SerializerMethodField('pagination_tagged_user')
    uploaded_by = serializers.SerializerMethodField('uploaded')
    mini_caption = serializers.SerializerMethodField('more_info')
    status_available = serializers.SerializerMethodField('check_status')

    def check_status(self, obj):
        try:
            request = self.context.get("request")
            if request.user == obj.uploaded_by:
                return False
            StatusMedia.objects.get(uploaded_by=obj.uploaded_by, visibility=False)
            return True
        except StatusMedia.DoesNotExist:
            return False

    def more_info(self, obj):
        if obj.commercial:
            validate_sponsorship =SponsoredUploadMultiple.objects.get(sponsored_post=obj).sponsored_post
            if obj == validate_sponsorship:
                return 'Sponsored'
        return obj.mini_caption

    def uploaded(self, obj):
        return str(obj.uploaded_by)
    
    def pagination_comment(self, obj):
        if obj.commentable is False:
            data_json = {
                'comment': False
            }
        else:
            comment = ImageComment.objects.filter(image_inst=obj).order_by("-created_on")
            serializer = ImageCommentSerializerMain(comment[:2], many=True)
            data_json = {
                'comment': True,
                'count': comment.count(), 
                'comments': serializer.data
                }
        return data_json

    def pagination_like(self, obj):
        like_image = LikeImage.objects.filter(image_inst=obj).order_by("-created_on")
        serializer = LikedImageSerializer(like_image[:2], many=True)
        data_json = {
            'count': like_image.count(),
            'likes': serializer.data
            }
        return data_json

    def pagination_tagged_user(self, obj):
        tagged_user = TaggedUser.objects.filter(added_media=obj).order_by("-created_on")
        serializer = TaggedUserSerializer(tagged_user[:2], many=True)
        data_json = {
            'count': tagged_user.count(),
            'tags': serializer.data
            }
        return data_json

    class Meta:
        model = NewUploadMultiple
        fields = ['id', 'title', 'uploaded_by', 'created_on', 'mini_caption', 'status_available', 'media_list', 'tagged_list', 'liked_list', 'comment_list' ]


class UserSerializer(serializers.ModelSerializer): 
    class Meta:
        model = User
        fields = ("first_name", "username", "email")


class UserSearchSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField('show_followers') 
    following = serializers.SerializerMethodField('show_following') 
    posts = serializers.SerializerMethodField('show_post') 

    def show_followers(self, obj):
        try:
            follow  = AllianceList.objects.filter(following=obj).count()
        except TypeError:
            pass
        return follow

    def show_following(self, obj):
        try:
            follow  = AllianceList.objects.filter(pilot=obj).count()
        except TypeError:
            pass
        return follow

    def show_post(self, obj):
        try:
            post  = NewUploadMultiple.objects.filter(uploaded_by=obj).count()
        except TypeError:
            pass
        return post

    class Meta:
        model = User
        fields = ['first_name', 'username', 'followers', 'following', 'posts']


class AllianceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllianceList
        fields = ['pilot', 'following']


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ['cover_image']


class SavedMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedMedia
        fields = ['saved_item', 'users_instance', 'collection_name']


class AllianceFollowersSerializer(serializers.ModelSerializer):
    following = serializers.SerializerMethodField()
    following_back = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField('get_profile_picture')

    def get_following(self, obj):
        return obj.following.username

    def get_following_back(self, obj):
        try:
            follow_back  = AllianceList.objects.get(pilot=obj.following, following=obj.pilot)
            follow_back = True
        except AllianceList.DoesNotExist:
            follow_back = False
        return follow_back

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(Profile.objects.get(user=obj.following).cover_image.url)

    class Meta:
        model = AllianceList
        fields = ['following', 'following_back', 'profile_picture']


class AllianceFollowingSerializer(serializers.ModelSerializer):
    follower = serializers.SerializerMethodField()
    following_back = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField('get_profile_picture')

    def get_follower(self, obj):
        return obj.pilot.username.lower()

    def get_following_back(self, obj):
        try:
            follow_back  = AllianceList.objects.get(following=obj.following, pilot=obj.pilot)
            follow_back = True
        except AllianceList.DoesNotExist:
            follow_back = False
        return follow_back

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(Profile.objects.get(user=obj.pilot).cover_image.url)

    class Meta:
        model = AllianceList
        fields = ['follower', 'following_back', 'profile_picture']


class ProfileDisplaySerializer(serializers.ModelSerializer):
    media_list = ImageGalerySerializer(many=True, read_only=True)
    uploaded_by = serializers.SerializerMethodField()

    def get_uploaded_by(self, obj):
        return obj.uploaded_by.username

    class Meta:
        model = NewUploadMultiple
        fields = ['id', 'uploaded_by', 'created_on',  'media_list']


class StatusSerializer(serializers.ModelSerializer):
    media_list = ImageGalerySerializer(many=True, read_only=True)
    uploaded_by = serializers.SerializerMethodField()

    def get_uploaded_by(self, obj):
        return obj.uploaded_by.username

    class Meta:
        model = StatusMedia
        fields = ['id', 'uploaded_by', 'created_on',  'media_list']