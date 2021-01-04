from django.shortcuts import render, redirect
from .models import ImageGalery, NewUploadMultiple, LikeImage, ImageComment, AllianceList, SavedMedia, TaggedUser, StatusMedia, StatusMediaGallery, BlockedUser, CollectionName, SponsoredUploadMultiple, LikeComment
from rest_framework import generics
from .serializers import ImageGalerySerializer, NewUploadMultipleSerializer, LikedImageSerializer, ImageCommentSerializer, StatusSerializer, UserSearchSerializer, ProfileDisplaySerializer, UserSerializer, AllianceFollowersSerializer, AllianceFollowingSerializer, ProfileSerializer, SavedMediaSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from .checkfile import video_list, photo_list
from .algorithm import display_media
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from pathlib import Path
from accounts.models import Profile
from rest_framework.authtoken.models import Token
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from re import search
from django.core.cache import cache
import os
import ast
import itertools
import hashlib

@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def home(request):
    return render(request, 'index.html')

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def api_root(request, format=None):
    return Response({
        'users': reverse('uploadimages', request=request, format=format),
        'snippets': reverse('home', request=request, format=format)
    })

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def show_image_fk(request):
    # queryset = NewUploadMultiple.objects.all()
    qs = NewUploadMultiple.objects.all()
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = paginator.paginate_queryset(qs, request)
    serialised_data = NewUploadMultipleSerializer(queryset, context={'request': request}, many=True)
    return paginator.get_paginated_response(serialised_data.data)
    # return Response(serialised_data.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def home_view(request):
    try:
        user = request.user
    except TypeError:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        tbv = AllianceList.objects.filter(following=user)
        follow_list_qs = []
        for i in tbv:
            follow_list_qs.append(i.following)
    except AllianceList.DoesNotExist:
        return Response({'error': 'Invalid follower list request'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        blocked_list = BlockedUser.objects.filter(pilot=user)
        bl = []
        for i in blocked_list:
            bl.append(i.blocked)
    except:
        return Response({'error': 'Blocked user cannot be accessed'}, status=status.HTTP_403_FORBIDDEN)

    follower_queryset = []
    follower_queryset.append(user)
    for follow_list in tbv:
        if follow_list.pilot not in bl:
            follower_queryset.append(follow_list.pilot)
    
    follower_media = NewUploadMultiple.objects.filter(uploaded_by__in=follower_queryset, commercial=False).order_by("-created_on")
    sponsored_post = NewUploadMultiple.objects.filter(commercial=True).order_by("-created_on")
    
    try:
        # follower_media = display_media(follower_media, sponsored_post)
        follower_media = NewUploadMultiple.objects.filter(uploaded_by__in=follower_queryset, commercial=False).order_by("-created_on")
    except AssertionError:
        return Response({'error': 'Invalid media request result'}, status=status.HTTP_400_BAD_REQUEST)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = paginator.paginate_queryset(follower_media, request)
    serialised_data = NewUploadMultipleSerializer(queryset, context={'request': request}, many=True)
    # print(serialised_data)
    return paginator.get_paginated_response(serialised_data.data)
    # return Response(serialised_data.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@login_required
def check_upload_status(request):
    progress = request.query_params.get('progress')
    serialized_data = {
        'status': cache.get(progress)
    }
    return Response(serialized_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def home_view_status(request):
    user =  request.user
    try:
        tbv = AllianceList.objects.filter(following=user)
    except AllianceList.DoesNotExist:
        return Response({'error': 'Invalid follower list request'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        blocked_list = BlockedUser.objects.filter(pilot=user)
    except:
        return Response({'error': 'Blocked user cannot be accessed'}, status=status.HTTP_403_FORBIDDEN)

    follower_queryset = []
    follower_queryset.append(user)
    for follow_list in tbv:
        if follow_list.pilot not in blocked_list:
            follower_queryset.append(follow_list.pilot)

    try:
        follower_media = StatusMedia.objects.filter(visibility=True, uploaded_by__username__in=follower_queryset).order_by("uploaded_by", "created_on")
        serialised_data = NewUploadMultipleSerializer(follower_media, context={'request': request}, many=True)
        return Response(serialised_data.data, status=status.HTTP_200_OK)
    except StatusMedia.DoesNotExist:
        return Response({'error': 'Invalid media request result'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def block_request(request):
    user = request.query_params.get('user') 
    try:
        BlockedUser.objects.create(
            pilot=request.user,
            blocked=User.objects.get(username=user)
        )
    except AssertionError:
        return Response({'error': 'Operation could not be completed'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': '%s does not exist' %user}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def search_view(request):
    search_params = request.query_params.get('result')
    serialized_data = {}

    try:
        hashtag_queryset  = NewUploadMultiple.objects.filter(title__icontains=search_params, commercial=False)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        queryset = paginator.paginate_queryset(hashtag_queryset, request)
        serialized_dt = NewUploadMultipleSerializer(queryset, context = {'request':request}, many=True)
        serialized_data['Post'] = serialized_dt.data
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Search could not be found'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_queryset  = User.objects.filter(username__icontains=search_params) | User.objects.filter(first_name__icontains=search_params)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        queryset = paginator.paginate_queryset(user_queryset, request)
        serialized_dt = UserSearchSerializer(queryset, context = {'request':request}, many=True)
        serialized_data['profile'] = serialized_dt.data
        return paginator.get_paginated_response(serialized_data)
    except User.DoesNotExist:
        return Response({'error': 'Search could not be found'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def delete_status(request):
    queryset = StatusMedia.objects.all()
    for qs in  queryset:
        date_check = qs.created_on - timedelta(days=1) 
        remove_media = timezone.now() > date_check
        if remove_media:
            queryset = StatusMedia.objects.get(id=qs.id)
            queryset.visibility = False
            queryset.save()

'''
Follow request/user user reaction
'''
@api_view(['POST'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def follow_request(request):
    user =  request.query_params.get('user')

    try:
        user_query = User.objects.get(username__iexact=user)
        user_query_self = request.user
    except User.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        following_check = AllianceList.objects.get(following=user_query_self, pilot=user_query)
        following_check.delete()
        return Response({'success': 'You are unfollowed %s' %str(following_check.pilot.username)}, status=status.HTTP_208_ALREADY_REPORTED)
    except AllianceList.DoesNotExist:
        following_check = AllianceList.objects.create(following=user_query_self, pilot=user_query)
        return Response({'success': 'You are following %s' %str(following_check.pilot.username)}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def following_request_display(request):
    user = request.query_params.get('user')
    user_query = User.objects.get(username__iexact=user)
    # user_query = request.user

    try:
        followers = AllianceList.objects.filter(following=user_query)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        queryset = paginator.paginate_queryset(followers, request)
        follow_list = AllianceFollowingSerializer(queryset, context={'request': request}, many=True)
        serialised_data = {
            'follow_list' : follow_list.data
        }
        # return Response(serialised_data, status=status.HTTP_200_OK)
        return paginator.get_paginated_response(serialised_data)
    except AllianceList.DoesNotExist:
        return Response({'error': 'Could not display following list'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def followers_request_display(request):
    user = request.query_params.get('user')
    user_query = User.objects.get(username__iexact=user)
    # user_query = request.user

    try:
        following = AllianceList.objects.filter(pilot=user_query)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        queryset = paginator.paginate_queryset(following, request)
        follow_list = AllianceFollowersSerializer(queryset, context={'request': request}, many=True)
        serialised_data = {
            'follow_list' : follow_list.data
        }
        # return Response(serialised_data, status=status.HTTP_200_OK)
        return paginator.get_paginated_response(serialised_data)
    except AllianceList.DoesNotExist:
        return Response({'error': 'Could not display followers list'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def user_show(request):
    # user =  request.query_params.get('user')

    try:
        user = request.user
        user_query = Profile.objects.get(user=user)
        follow_list = ProfileSerializer(user_query, context={'request': request})
        serialised_data = {
            'follow_list' : follow_list.data
        }
        return Response(serialised_data, status=status.HTTP_200_OK)
        # return paginator.get_paginated_response(serialised_data)
    except User.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        

'''
Show profile
'''
@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def profile_page(request):
    if request.user.is_authenticated:
        user_query = request.user
    else:
        return Response({'error': 'Not logged in'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        followers = AllianceList.objects.filter(pilot=user_query).count()
        following = AllianceList.objects.filter(following=user_query).count()
    except AllianceList.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        saved_media = SavedMedia.objects.filter(users_instance=user_query).count()
    except SavedMedia.DoesNotExist:
        return Response({'error': 'Somenthing is wrong with saved data'}, status=status.HTTP_404_NOT_FOUND)

    try:
        media_queryset = NewUploadMultiple.objects.filter(uploaded_by=user_query).order_by("created_on")
        paginator = PageNumberPagination()
        paginator.page_size = 10
        queryset = paginator.paginate_queryset(media_queryset, request)
        media_list = ProfileDisplaySerializer(queryset, context={'request': request}, many=True)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Post request is wrongly requested'}, status=status.HTTP_400_BAD_REQUEST)

    try:    
        serialised_data = {
            'username': user_query.username,
            'fullname': user_query.first_name,
            'following': following,
            'followers': followers,
            'saved': saved_media,
            'post': media_queryset.count(),
            'media': media_list.data
        }
        return Response(serialised_data, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Something when wrong with your request'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def profile_page_others(request):
    user =  request.query_params.get('user')
    detect_self = False    

    try:
        user_query = User.objects.get(username__iexact=user)
        # user_query_self = User.objects.get(username__iexact=user_self)
        user_query_self = request.user
    except User.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    if user_query == user_query_self:
        detect_self = True    
    try:
        followers = AllianceList.objects.filter(pilot=user_query).count()
        following = AllianceList.objects.filter(following=user_query).count()
    except AllianceList.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        followers_check = AllianceList.objects.filter(pilot=user_query, following=user_query_self).exists()
        following_check = AllianceList.objects.filter(following=user_query, pilot=user_query_self).exists()
    except AllianceList.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        saved_media = SavedMedia.objects.filter(users_instance=user_query).count()
    except SavedMedia.DoesNotExist:
        return Response({'error': 'Somenthing is wrong with saved data'}, status=status.HTTP_404_NOT_FOUND)

    try:
        media_queryset = NewUploadMultiple.objects.filter(uploaded_by=user_query, commercial=False).order_by("created_on")
        paginator = PageNumberPagination()
        paginator.page_size = 10
        queryset = paginator.paginate_queryset(media_queryset, request)
        media_list = ProfileDisplaySerializer(queryset, context={'request': request}, many=True)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Post request is wrongly requested'}, status=status.HTTP_400_BAD_REQUEST)

    try:    
        serialised_data = {
            'username': user_query.username,
            'fullname': user_query.first_name,
            'self': detect_self,
            'following': following,
            'followers': followers,
            'following_user': followers_check, 
            'following_user_back': following_check,
            'saved': saved_media,
            'post': media_queryset.count(),
            'media': media_list.data
        }
        return Response(serialised_data, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Something when wrong with your request'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def likeimage(request):
    # user =  request.query_params.get('user')
    media_id = request.query_params.get('media_id')

    try:
        username = request.user
    except User.DoesNotExist:
        return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        img_instance =  NewUploadMultiple.objects.get(id=media_id)
    except:
        return Response({'error': 'Post does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try: 
        like_inst_check = LikeImage.objects.filter(
            image_inst = img_instance,
            user = username
        )
        if like_inst_check.exists():
            like_inst_check.delete()
            return Response({'success': 'unliked'}, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Your like was not updated' }, status=status.HTTP_400_BAD_REQUEST)

    try:    
        like_added = LikeImage.objects.create(
            image_inst = img_instance,
            user = username
        )
    except:
        return Response({'error': 'Your like was not posted' }, status=status.HTTP_400_BAD_REQUEST)

    serialised_data = LikedImageSerializer(instance=like_added)
    if serialised_data:
        serialised_data.data
        return Response({'success': 'liked'}, status=status.HTTP_201_CREATED)
    else:
        return Response(serialised_data.data, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def media_file_single(request):
    media_id = request.query_params.get('media_id')
    try:
        queryset = ImageGalery.objects.filter(pk=media_id)
        serialised_data = ImageGalerySerializer(queryset, context={'request': request}, many=True)
        return Response(serialised_data.data, status=status.HTTP_200_OK)
    except ImageGalery.DoesNotExist:
        return Response({'error':'Cannot find media file'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def media_file(request):
    media_id = request.query_params.get('media_id')
    try:
        queryset = NewUploadMultiple.objects.get(pk=media_id)
        serialised_data = NewUploadMultipleSerializer(queryset, context={'request': request})
        return Response(serialised_data.data, status=status.HTTP_200_OK)
    except:
        return Response({'error':'Cannot find media file'}, status=status.HTTP_404_NOT_FOUND)


'''
Commenting codes
'''
@api_view(['POST'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def make_comment(request):
    try:
        comment = request.data['comment']
        media_id = request.query_params.get('media_id')
        parent_id = request.query_params.get('parent_id')
        if parent_id is None or len(parent_id) <= 0:
            parent_id = None
        else:
            parent_id = int(parent_id)

    except:
        return Response({'error': 'Invalid parse json value'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        insterted_image = NewUploadMultiple.objects.get(pk=media_id)
    except:
        return Response({'error': 'Media does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if parent_id:
            parent_obj = ImageComment.objects.get(id=parent_id)
            if parent_obj.parent is None:
                pass
            else:
                parent_obj = parent_obj.parent
            comment_made = ImageComment.objects.create(
                image_inst = insterted_image,
                comment = comment,
                comment_by = request.user,
                parent = parent_obj
            )
        else:
            comment_made = ImageComment.objects.create(
                image_inst = insterted_image,
                comment = comment,
                comment_by = request.user,
            )
        comment_made.save()
        return Response({'success': 'Your comment has been made'}, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Unable to add your comment at the moment'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def like_comment(request):
    comment_id = request.query_params.get('comment_id')
    try:
        insterted_image = ImageComment.objects.get(pk=comment_id)
    except:
        return Response({'error': 'Comment does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        liked_instance = LikeComment.objects.get(
            comment_inst = insterted_image,
            user = request.user
        )
        liked_instance.delete()
        return Response({'success': 'Your comment has been unliked'}, status=status.HTTP_201_CREATED)
    except LikeComment.DoesNotExist:
        liked_instance = LikeComment.objects.create(
            comment_inst = insterted_image,
            user = request.user
        )
        liked_instance.save()
        return Response({'success': 'Your comment has been liked'}, status=status.HTTP_201_CREATED)
    except TypeError:
        return Response({'error': 'Unable to add your comment like at the moment'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def show_comments(request):
    image_pk = request.query_params.get('image_id')
    parent_id = request.query_params.get('parent_id')
    if parent_id is None or len(parent_id) <= 0:
        parent_id = None
    else:
        parent_id = int(parent_id)

    try:
        img_instance = NewUploadMultiple.objects.get(pk=image_pk)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Media Does not exist'}, status=status.HTTP_404_NOT_FOUND)
    try:
        if parent_id:
            parent_obj = ImageComment.objects.get(id=parent_id)
            qs = ImageComment.objects.filter(image_inst=img_instance, parent=parent_obj).order_by("-created_on")
        else:
            qs = ImageComment.objects.filter(image_inst=img_instance, parent__isnull=True).order_by("-created_on")
    except ImageComment.DoesNotExist:
        return Response({'error': 'Error in image comment'}, status=status.HTTP_400_BAD_REQUEST)
    
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = paginator.paginate_queryset(qs, request)
    json_data = ImageCommentSerializer(queryset, context={'request': request}, many=True)

    return paginator.get_paginated_response(json_data.data)

@api_view(['GET'])
# @permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def commentable(request):
    try:
        media_id = request.query_params('media_id')
    except:
        return Response({'error': 'Invalid parse json value'}, status=status.HTTP_400_BAD_REQUEST)
    registerd_user = request.user
    try:
        insterted_image = NewUploadMultiple.objects.get(pk=media_id, uploaded_by=registerd_user)
        if insterted_image.commentable:
            insterted_image.commentable = False
            insterted_image.save()
            return Response({'success': 'Your comment field is disabled'}, status=status.HTTP_201_CREATED)
        else:
            insterted_image.commentable = True
            insterted_image.save()
            return Response({'success': 'Your comment field is enabled'}, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Media does not exist'}, status=status.HTTP_400_BAD_REQUEST)


'''
Uploading and modifying of media post
'''
@api_view(['POST'])
# @permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def upload_media(request):
    if request.user.is_authenticated:
        # print(request.user)
        try:
            try:
                user = request.data['user']
                title = request.data['title'] 
                media_file = dict((request.data).lists())['media_file']
                taglist = request.data['tag_list']
                if len(user) < 0:
                    return Response({'error': 'Please provide user and title information'}, status=status.HTTP_400_BAD_REQUEST)

            except:
                return Response({'error': 'Invalid parse json value'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user_query = User.objects.get(username__iexact='miebaka')
                # user_query = request.user
            except User.DoesNotExist:
                return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                insterted_image = NewUploadMultiple.objects.create(
                    title = title,
                    uploaded_by = user_query
                ) 
            except NewUploadMultiple.DoesNotExist:
                return Response({'error': 'Error in saving media in database'}, status=status.HTTP_404_NOT_FOUND)     

            tag_post = False
            if len(taglist) > 0:
                tag_post = True
            res = taglist.strip('][').split(',')
            res = list(dict.fromkeys(res))
            if tag_post:
                for tg in res:
                    try:
                        tg_user = User.objects.get(username__iexact=tg.strip(' '))
                        if tg_user is not user_query:
                            tg_queryset = TaggedUser.objects.create(
                                added_media = insterted_image,
                                users_instance = tg_user
                            ) 
                    except User.DoesNotExist:
                        tg_queryset.delete()
                        insterted_image.delete()
                        return Response({'error': 'Tagged user does not exist'}, status=status.HTTP_404_NOT_FOUND)

            file_format = []
            for imgs in media_file:
                file_extension = Path(str(imgs)).suffix
                if file_extension.lower() in photo_list:
                    file_format.append('image')
                elif file_extension.upper() in video_list:
                    file_format.append('video')
                else:
                    insterted_image.delete()
                    return Response({'error': 'Error with media format'}, status=status.HTTP_400_BAD_REQUEST)

            for (imgs, format_type) in itertools.zip_longest(media_file, file_format):
                try:
                    if ImageGalery.objects.filter(media_file__icontains=str(imgs)).exists():
                        media_object = ImageGalery.objects.create(
                        # media_object = ImageGalery(
                            image_inst = insterted_image,
                            media_file = '%s%s'%(settings.UPLOAD_PATH, str(imgs)),
                            file_type = format_type
                        )
                    else:
                        media_object = ImageGalery.objects.create(
                            image_inst = insterted_image,
                            media_file = imgs,
                            file_type = format_type
                        )
                        media_object.new_upload_save()
                except:
                    insterted_image.delete()
                    tg_queryset.delete()
                    media_object.delete()
                    return Response({'error': 'Error in saving media in database'}, status=status.HTTP_400_BAD_REQUEST)

            serialised_data = NewUploadMultipleSerializer(insterted_image, context={'request': request})
            if serialised_data:
                # serialised_data.data
                return Response(serialised_data.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serialised_data.data, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'Error in saving media in database, double check json index'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'You must sign in'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
# @permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def upload_media_sponsor(request):
    if request.user.is_superuser is False:
        return Response({'error': 'Not enough admin privilaged'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if request.user.is_authenticated:
        # print(request.user)
        try:
            try:
                title = request.data['title'] 
                user = request.data['user']
                option = request.data['option']
                option_url = request.data['option_url']
                media_file = dict((request.data).lists())['media_file']
                taglist = request.data['tag_list']
                if len(user) < 0:
                    return Response({'error': 'Please provide user and title information'}, status=status.HTTP_400_BAD_REQUEST)

            except:
                return Response({'error': 'Invalid parse json value'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user_query = User.objects.get(username__iexact=user)
                # user_query = request.user
            except User.DoesNotExist:
                return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                insterted_image = NewUploadMultiple.objects.create(
                    title = title,
                    detail = option,
                    detail_url = option_url,
                    commercial= True,
                    uploaded_by = user_query
                ) 
            except NewUploadMultiple.DoesNotExist:
                return Response({'error': 'Error in saving media in database'}, status=status.HTTP_404_NOT_FOUND)     

            tag_post = False
            if len(taglist) > 0:
                tag_post = True
            res = taglist.strip('][').split(',')
            res = list(dict.fromkeys(res))
            if tag_post:
                for tg in res:
                    try:
                        tg_user = User.objects.get(username__iexact=tg.strip(' '))
                        if tg_user is not user_query:
                            tg_queryset = TaggedUser.objects.create(
                                added_media = insterted_image,
                                users_instance = tg_user
                            ) 
                    except User.DoesNotExist:
                        tg_queryset.delete()
                        insterted_image.delete()
                        return Response({'error': 'Tagged user does not exist'}, status=status.HTTP_404_NOT_FOUND)

            file_format = []
            for imgs in media_file:
                file_extension = Path(str(imgs)).suffix
                if file_extension.lower() in photo_list:
                    file_format.append('image')
                elif file_extension.upper() in video_list:
                    file_format.append('video')
                else:
                    insterted_image.delete()
                    return Response({'error': 'Error with media format'}, status=status.HTTP_400_BAD_REQUEST)

            for (imgs, format_type) in itertools.zip_longest(media_file, file_format):
                try:
                    if ImageGalery.objects.filter(media_file__icontains=str(imgs)).exists():
                        media_object = ImageGalery.objects.create(
                        # media_object = ImageGalery(
                            image_inst = insterted_image,
                            media_file = '%s%s'%(settings.UPLOAD_PATH, str(imgs)),
                            file_type = format_type
                        )
                    else:
                        media_object = ImageGalery.objects.create(
                            image_inst = insterted_image,
                            media_file = imgs,
                            file_type = format_type
                        )
                        media_object.new_upload_save()
                except:
                    insterted_image.delete()
                    tg_queryset.delete()
                    media_object.delete()
                    return Response({'error': 'Error in saving media in database'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                SponsoredUploadMultiple.objects.create(
                    sponsored_post=insterted_image,
                    uploaded_by=request.user
                )
            except:
                insterted_image.delete()
                tg_queryset.delete()
                media_object.delete()
                return Response({'error': 'Not enough admin privilaged'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            serialised_data = NewUploadMultipleSerializer(insterted_image, context={'request': request})
            if serialised_data:
                # serialised_data.data
                return Response(serialised_data.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serialised_data.data, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'Error in saving media in database, double check json index'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'You must sign in'}, status=status.HTTP_401_UNAUTHORIZED)


def generate_media_path(filename):
    filename, ext = os.path.splitext(filename.lower())
    filename = "%s.%s" %(slugify(filename),timezone.now())
    hs_index = hashlib.md5(filename.encode())
    filename = "%s%s" %(hs_index.hexdigest(), ext)
    # print(filename)
    return filename
        # return "%s/%s" %(UPLOAD_PATH, filename)


@api_view(['POST'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def upload_media_status(request):
    try:
        try:
            user = request.data['user']
            title = request.data['title'] 
            media_file = dict((request.data).lists())['media_file']
            taglist = request.data['tag_list']
            if len(user) < 0 or len(title) < 0:
                return Response({'error': 'Please provide user and title information'}, status=status.HTTP_400_BAD_REQUEST)

        except:
            return Response({'error': 'Invalid parse json value'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_query = request.user
            # user_query = User.objects.get(username__iexact=user)
        except User.DoesNotExist:
            return Response({'error': 'User Does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            insterted_image = StatusMedia.objects.create(
                title = title,
                uploaded_by = user_query
            ) 
        except StatusMedia.DoesNotExist:
            return Response({'error': 'Error in saving media in database'}, status=status.HTTP_404_NOT_FOUND)     

        tag_post = False
        if len(taglist) > 0:
            tag_post = True
        res = taglist.strip('][').split(',')
        res = list(dict.fromkeys(res))
        if tag_post:
            for tg in res:
                try:
                    tg_user = User.objects.get(username__iexact=tg.strip(' '))
                    if tg_user is not user_query:
                        tg_queryset = TaggedUser.objects.create(
                            added_media = insterted_image,
                            users_instance = tg_user
                        ) 
                except User.DoesNotExist:
                    tg_queryset.delete()
                    insterted_image.delete()
                    return Response({'error': 'Tagged user does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        file_format = []
        for imgs in media_file:
            file_extension = Path(str(imgs)).suffix
            if file_extension.lower() in photo_list:
                file_format.append('image')
            elif file_extension.upper() in video_list:
                file_format.append('video')
            else:
                insterted_image.delete()
                return Response({'error': 'Error with media format'}, status=status.HTTP_400_BAD_REQUEST)

        for (imgs, format_type) in itertools.zip_longest(media_file, file_format):
            try:
                if StatusMediaGallery.objects.filter(media_file__icontains=str(imgs)).exists():
                    media_object = StatusMediaGallery.objects.create(
                        image_inst = insterted_image,
                        media_file = '%s%s'%(settings.UPLOAD_PATH, str(imgs)),
                        file_type = format_type
                    )
                else:
                    media_object = StatusMediaGallery.objects.create(
                        image_inst = insterted_image,
                        media_file = imgs,
                        file_type = format_type
                    )
            except:
                insterted_image.delete()
                tg_queryset.delete()
                media_object.delete()
                return Response({'error': 'Error in saving media in database'}, status=status.HTTP_400_BAD_REQUEST)

        serialised_data = StatusSerializer(insterted_image, context={'request': request})
        if serialised_data:
            # serialised_data.data
            return Response(serialised_data.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serialised_data.data, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'error': 'Error in saving media in database, double check json index'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def delete_media(request):
    try:
        # user = request.query_params('user')
        image_id = request.query_params('id')
    except:
        return Response({'error': 'Error in parsing json'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # user_query = User.objects.get(username__iexact=user)
        user_query = request.user
    except User.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_404_NOT_FOUND)
    try:
        media_insta =  NewUploadMultiple.objects.get(uploaded_by=user_query, pk=image_id)
        media_insta.delete
        return Response({'success': 'Post has been delected successfully'},status=200)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Post does not exist'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def update_media(request):
    try:
        # user = request.query_params('user')
        image_id = request.query_params('id')
        updated_title = request.data['title']
    except:
        return Response({'error': 'Error in parsing json'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # user_query = User.objects.get(username__iexact=user)
        user_query = request.user
    except User.DoesNotExist:
        return Response({'error': 'User Does not exist'}, status=status.HTTP_404_NOT_FOUND)

    try:
        media_insta =  NewUploadMultiple.objects.get(uploaded_by=user_query, pk=image_id)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Media file does not exist'}, status=status.HTTP_404_NOT_FOUND)

    try:
        media_insta.title = updated_title
        media_insta.save()
        # serialised_data = NewUploadMultipleSerializer(instance=media_insta)
        serialised_data = NewUploadMultipleSerializer(instance=media_insta, context={'request':request})
        if serialised_data:
            serialised_data.data
            return Response(serialised_data.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serialised_data.data, status=status.HTTP_400_BAD_REQUEST)
        # return Response({'success': 'Post has been delected successfully'},status=200)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Error in delecting post'}, status=status.HTTP_400_BAD_REQUEST)


'''
check user active status
'''
@api_view(['GET'])
@login_required
def last_seen(request):

    user = request.query_params.get('user')
    try:
        user_state = Profile.objects.get(user=User.objects.get(username__iexact=user))
    except (User.DoesNotExist, Profile.DoesNotExist):
        return Response({'error': 'User Does not exist'}, status=status.HTTP_404_NOT_FOUND)
    
    try:   
        serialised_data = {
            'status': user_state.online,
            'time' : user_state.last_seen_algorithm
        }
        return Response(serialised_data, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Something when wrong with your request'}, status=status.HTTP_400_BAD_REQUEST)


'''
This part is for saved media and collection naming
'''
@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def show_saved_media(request):
    media_qs = SavedMedia.objects.filter(users_instance=request.user)
    save_list = []
    for sl in media_qs:
        save_list.append(sl.saved_item.id)
    # return Response(status=200)
    saved_media_qs = NewUploadMultiple.objects.filter(id__in=save_list)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = paginator.paginate_queryset(saved_media_qs, request)
    serialised_data = NewUploadMultipleSerializer(queryset, context={'request': request}, many=True)
    return paginator.get_paginated_response(serialised_data.data)

@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def show_specific_saved_media(request):
    collection = request.query_params.get('collection_field')
    try:
        coll_qs = CollectionName.objects.filter(pilot=request.user, collection=collection)
        media_qs = SavedMedia.objects.filter(users_instance=request.user, collection_name=coll_qs)
    except (SavedMedia.DoesNotExist, CollectionName.DoesNotExist):
        return Response({'error': 'Unable to access post'}, status=status.HTTP_400_BAD_REQUEST)        
    save_list = []
    for sl in media_qs:
        save_list.append(sl.saved_item.id)
    saved_media_qs = NewUploadMultiple.objects.filter(id__in=save_list)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    queryset = paginator.paginate_queryset(saved_media_qs, request)
    serialised_data = NewUploadMultipleSerializer(queryset, context={'request': request}, many=True)
    return paginator.get_paginated_response(serialised_data.data)


@api_view(['GET'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticated,))
@login_required
def save_media(request):
    try:
        # user = request.query_params.get('user')
        image_id = request.query_params.get('id')
    except:
        return Response({'error': 'Error in parsing json'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        # user_query = User.objects.get(username__iexact=user)
        user_query = request.user
    except User.DoesNotExist:
        return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
    try:
        media_insta =  NewUploadMultiple.objects.get(pk=image_id)
        validate_saved = SavedMedia.objects.filter(
            saved_item = media_insta,
            users_instance = user_query
        ).exists()
        if validate_saved:
            return Response({'success': 'Media is already saved'}, status=status.HTTP_208_ALREADY_REPORTED)
        else:
            SavedMedia.objects.create(
                saved_item = media_insta,
                users_instance = user_query
            )
        return Response({'success': 'Post has been saved successfully'}, status=status.HTTP_201_CREATED)
    except NewUploadMultiple.DoesNotExist:
        return Response({'error': 'Unable to access post'}, status=status.HTTP_400_BAD_REQUEST)
    except SavedMedia.DoesNotExist:
        return Response({'error': 'Unable to save post'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@login_required
def create_collection(request):
    try:
        collection_name = request.data['collection_name']
    except:
        return Response({'error': 'Invalid json data'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        new_collection = CollectionName.objects.create(pilot=request.user, collection=collection_name)
        new_collection.save()
        serialized_data = {
            'success': '%s has been created successfully' %new_collection.collection,
            'id': new_collection.id

        }
        return Response(serialized_data, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Invalid media request result'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@login_required
def add_collection(request):
    try:
        collection_id = request.data['collection_id']
        saved_media_id = request.data['saved_media_id']

    except:
        return Response({'error': 'Invalid json data'}, status=status.HTTP_403_FORBIDDEN)

    saved_media = saved_media_id.strip('][').split(',')
    saved_media_list = list(dict.fromkeys(saved_media))
    try:
        new_collection = CollectionName.objects.get(id=collection_id)
        for media_list in saved_media_list:
            try:
                SavedMedia.objects.get(
                    saved_item=NewUploadMultiple.objects.get(id=media_list), 
                    collection_name=new_collection,
                    users_instance=request.user)
            except SavedMedia.DoesNotExist:
                saved_media = SavedMedia.objects.create(
                    saved_item=NewUploadMultiple.objects.get(id=media_list), 
                    collection_name=new_collection,
                    users_instance=request.user)
            except NewUploadMultiple.DoesNotExist:
                saved_media.delete()
                return Response({'error': 'could not get media post'}, status=status.HTTP_403_FORBIDDEN)
        queryset = SavedMedia.objects.filter(collection_name=new_collection, users_instance=request.user).order_by('created_on')
        serialized_data = SavedMediaSerializer(queryset, context={'request': request}, many=True)
        return Response(serialized_data.data, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Invalid media request result'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@login_required
def edit_collection(request):
    try:
        collection_id = request.data['collection_id']
        collection_name = request.data['collection_name']
    except:
        return Response({'error': 'Invalid json data'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        new_collection = CollectionName.objects.get(id=collection_id)
        new_collection.collection=collection_name
        new_collection.save()

        queryset = SavedMedia.objects.filter(collection_name=new_collection).order_by('created_on')            
        serialized_data = {
            'success': '%s has been created successfully' %new_collection.collection,
            'id': new_collection.id
        }
        return Response(serialized_data, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Invalid media request result'}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
@login_required
def delete_collection(request):
    try:
        collection_id = request.data['collection_id']
    except:
        return Response({'error': 'Invalid json data'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        new_collection = CollectionName.objects.get(id=collection_id)
        new_collection.delete()
        serialized_data = {
            'success': 'Delete successful' 
        }
        return Response(serialized_data, status=status.HTTP_201_CREATED)
    except:
        return Response({'error': 'Invalid media request result'}, status=status.HTTP_400_BAD_REQUEST)