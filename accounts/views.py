from django.contrib.auth.models import User
from django.contrib.auth import (login as auth_login,  authenticate, logout)
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from .serializers import UserSerializer
from rest_framework import serializers, status
from .models import Profile, LoginLogsheet
from config_project.config import OTP_KEY
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication, BasicAuthentication
from django.views.decorators.csrf import csrf_exempt
import pyotp
import base64

from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponseRedirect
# from django.contrib import messages
# from django.http import JsonResponse
import re
import string
import hashlib
from datetime import datetime
import time 

from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic import View, UpdateView
from django.urls import reverse_lazy
from django.contrib.sites.shortcuts import get_current_site

@api_view(['POST','GET'])
@permission_classes((AllowAny,))
# @login_required
def login(request):
    if request.user.is_authenticated:
        username = request.data['username']
        if str(request.user) == username:
            serialized_data = {
                'error': 'You are already logged in'
            }
        else:
            serialized_data = {
                {'error': 'user %s, already logged in' %str(request.user)}
            }
        return Response(serialized_data, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'POST':
        username = request.data['username']
        raw_password = request.data['password']
        user = authenticate(username=username, password=raw_password)
        if user is not None:
            user_profile = Profile.objects.get(user=user)
            if user_profile.email_confirmed != False:
                raise serializers.ValidationError({'error': 'User email is not verified, Please check email for activation link'})
            elif user.is_active is False:
                raise serializers.ValidationError({'error': 'User account in not activated'})
            else:
                if user_profile.two_step_verification:
                    user_profile.counter += 1  # Update Counter At every Call
                    user_profile.isVerified = False
                    user_profile.save()  # Save the data
                    rt_valu = str(user_profile.mobile) + str(datetime.date(datetime.now())) + OTP_KEY
                    key = base64.b32encode(rt_valu.encode())  # Key is generated
                    OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
                    serialized_data = {
                        'wait': True,
                        'token_wait': default_token_generator.make_token(user),
                        'otp': OTP.at(user_profile.counter)
                    }
                    return Response(serialized_data, status=status.HTTP_200_OK)
                else:
                    auth_login(request, user)
                    serialized_data = {
                        'wait': False,
                        "success":"Login Sucessful",
                    }
                    try:
                        LoginLogsheet.objects.create(user=request.user)
                    except TypeError:
                        pass
                    return Response(serialized_data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Invalid Password or account in not activated'}, status=status.HTTP_404_NOT_FOUND)
        
@csrf_exempt
@api_view(['POST'])
def login_with_otp(request):
    if request.user.is_authenticated:
        user = request.data['user']
        if str(request.user) == user:
            serialized_data = {
                'error': 'You are already logged in'
            }
        else:
            serialized_data = {
                {'error': 'user %s, already logged in' %str(request.user)}
            }
        return Response(serialized_data, status=status.HTTP_403_FORBIDDEN)
    try:
        user = request.data['user']
        otp = request.data['otp']
        token_wait = request.data['token_wait']
    except:
        return Response({'error': 'The registration was incomplete, try verifying all fields'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=user)
        user_profile = Profile.objects.get(user=user)
    except ObjectDoesNotExist:
        return Response({"error" : "User does not exist"}, status=404)  # False Call
    rt_valu = str(user_profile.mobile) + str(datetime.date(datetime.now())) + OTP_KEY
    key = base64.b32encode(rt_valu.encode())  # Generating Key
    OTP = pyotp.HOTP(key)  # HOTP Model
    if user_profile.isVerified:
        return Response({'error' : 'OTP is expired'}, status=status.HTTP_400_BAD_REQUEST)

    if OTP.verify(otp, user_profile.counter):  # Verifying the OTP
        user_profile.isVerified = True
        user_profile.save()
        try:
            if default_token_generator.check_token(user, token_wait):
                auth_login(request, user)
                LoginLogsheet.objects.create(user=request.user)
                serialized_data = {
                    "success":"Login Sucessful",
                }
                return Response(serialized_data, status=status.HTTP_200_OK)
            else:
                return Response({'error' : 'Unable to login'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error' : 'Unable to login'}, status=status.HTTP_400_BAD_REQUEST)
            
            
@api_view(['POST'])
def signup(request):
    if request.method == 'POST':
        try:
            username = request.data['username']
            full_name = request.data['full_name']
            password = request.data['password']
            raw_password = request.data['re_password']
            email_address = request.data['email']
            mobile = request.data['mobile']

            user_json_data = {
                "username" : request.data['username'],
                "full_name" : request.data['full_name'],
                "password" : request.data['password'],
                "raw_password" : request.data['re_password'],
                "email" : request.data['email']
            }

        except:
            return Response({'error': 'The registration was incomplete, try verifying all fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializers = UserSerializer(data=request.data, context={'request': request})
    
        if Profile.objects.filter(mobile=number).exists():
            raise serializers.ValidationError({'error': 'Phone number already exist'})

        if serializers.is_valid() is False:
            return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
        
        _available = User.objects.filter(username__iexact=username).exists() | User.objects.filter(email__iexact=email_address).exists()
        if password == raw_password:
            if _available == False:
                try:
                    user = User.objects.create_user(
                        username, 
                        email_address,
                        raw_password
                    )
                    user.first_name = full_name
                    user.is_active = True
                    user.save()
                    user_profile = Profile.objects.get(user=user)
                    user_profile.mobile = mobile
                    user_profile.save()
                    
                    return Response({'success': 'Your account has been created'}, status=status.HTTP_201_CREATED)
                except:
                    return Response({'error': 'Username could not be created'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif User.objects.filter(username__iexact=username).exists():
            return Response({'error': 'Username already exist'}, status=status.HTTP_400_BAD_REQUEST)

        elif User.objects.filter(email__iexact=email_address).exists():
            return Response({'error': 'Email already exist'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'error': 'Password does not match'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
# @permission_classes((IsAuthenticated,))
@login_required
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        return Response({'success' : 'Logged out'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'You need to login first'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@login_required
def change_password(request):
    if request.method == 'POST':

        password = request.data['password']
        user_intsance = request.user
        user_intsance.set_password(password)
        user_intsance.save()
        Token.objects.get(user=user_intsance).delete()
        tk_key = Token.objects.create(user=user_intsance).key

        data = {
            'success': 'Password changed successfully',
            # 'token': tk_key
        }
        return Response(data, status=status.HTTP_201_CREATED)

        old_password = request.data['old_password']
        password = request.data['password']
        re_password = request.data['re_password']

        if password != re_password:
            return Response({'error': 'Password does not match'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_intsance = request.user
            user_intsance.set_password(password)
            user_intsance.save()
            Token.objects.get(user=user_intsance).delete()
            tk_key = Token.objects.create(user=user_intsance).key

            data = {
                'success': 'Password changed successfully',
                # 'token': tk_key
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except:
            return Response({'error': 'Password cannot be changed at the moment'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_account_sms(request):
    if request.method == 'POST':
        mobile = request.data['mobile']
        user = request.data['user']
        _check_email = Profile.objects.get(mobile=mobile)
        user = User.objects.get(username__iexact=user)
        if user:
            try:
                Mobile = Profile.objects.get(mobile=mobile)  # if Mobile already exists the take this else create New One
            except ObjectDoesNotExist:
                return Response({'error': 'You have not valid phone number'}, status=status.HTTP_404_NOT_FOUND)
            Mobile.counter += 1  # Update Counter At every Call
            Mobile.isVerified=False
            Mobile.save()  # Save the data
            rt_valu = str(mobile) + str(datetime.date(datetime.now())) + OTP_KEY
            try:
                key = base64.b32encode(rt_valu.encode())  # Key is generated
                OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
                print('Your OTP is %s \nThank you for using IG Clone' %OTP.at(Mobile.counter))
                return Response({'success':'OTP has been sent to your modile device'}, status=status.HTTP_200_OK)
            except:
                return Response({'error':'Unable to send OTP at the moment'}, status=status.HTTP_400_BAD_REQUEST)
                
@api_view(['POST'])
def verify_account_email(request):
    if request.method == 'POST':
        mobile = request.data['mobile']
        user = request.data['user']
        _check_email = Profile.objects.get(mobile=mobile)
        user = User.objects.get(username__iexact=user)
        if user:
            subject = 'FACEBOOK'
            email_template_name = "validate_sms.txt"
            try:
                Mobile = Profile.objects.get(mobile=mobile)  # if Mobile already exists the take this else create New One
            except ObjectDoesNotExist:
                return Response({'error': 'You have no valid phone number'}, status=status.HTTP_404_NOT_FOUND)
            Mobile.counter += 1  # Update Counter At every Call
            Mobile.save()  # Save the data
            rt_valu = str(mobile) + str(datetime.date(datetime.now())) + OTP_KEY
            key = base64.b32encode(rt_valu.encode())  # Key is generated
            OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
            print('Your OTP is %s \nThank you for using IG Clone' %OTP.at(Mobile.counter))

            c = {
                "email":user.email,
                'domain':get_current_site(request),
                'site_name': 'FACEBOOK',
                'user': user,
                'otp_token': OTP.at(Mobile.counter),
                'protocol': 'http',
                }
            email = render_to_string(email_template_name, c)
            try:
                send_mail(subject, email, 'admin@example.com' , [user.email], fail_silently=False)
                return Response({'success':'OTP has been sent to your email to complete registration.'}, status=status.HTTP_200_OK)
            except:
                return Response({'error':'Unable to send OTP at the moment'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getopt(request):
    mobile = request.data['mobile']
    try:
        Mobile = Profile.objects.get(mobile=mobile)  # if Mobile already exists the take this else create New One
    except ObjectDoesNotExist:
        return Response({'error':'Number is not in database'}, status=status.HTTP_404_NOT_FOUND)
    Mobile.counter += 1  # Update Counter At every Call
    Mobile.isVerified = False
    Mobile.save()  # Save the data
    rt_valu = str(mobile) + str(datetime.date(datetime.now())) + OTP_KEY
    key = base64.b32encode(rt_valu.encode())  # Key is generated
    OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
    print(OTP.at(Mobile.counter))
    # Using Multi-Threading send the OTP Using Messaging Services like Twilio or Fast2sms
    return Response({"otp": OTP.at(Mobile.counter)}, status=status.HTTP_200_OK)  # Just for demonstration

@api_view(['POST'])
def verifyopt(request):
    mobile = request.data['mobile']
    try:
        Mobile = Profile.objects.get(mobile=mobile)
    except ObjectDoesNotExist:
        return Response({"error" : "User does not exist"}, status=404)  # False Call
    rt_valu = str(mobile) + str(datetime.date(datetime.now())) + OTP_KEY
    key = base64.b32encode(rt_valu.encode())  # Generating Key
    OTP = pyotp.HOTP(key)  # HOTP Model
    if Mobile.isVerified:
        return Response({'error' : 'OTP is expired'}, status=status.HTTP_400_BAD_REQUEST)

    if OTP.verify(request.data["otp"], Mobile.counter):  # Verifying the OTP
        Mobile.isVerified = True
        Mobile.save()
        return Response({'success' : 'You are authorised'}, status=status.HTTP_200_OK)
    return Response({'error' : 'OTP is wrong'}, status=status.HTTP_400_BAD_REQUEST)


@login_required
def modify_account(request):
    user = request.user
    name = request.data['name']
    username = request.data['username']
    website = request.data['website']
    bio = request.data['bio']
    email = request.data['email']
    number = request.data['number']
    sex = request.data['sex']
    cover_image = request.data['cover_image']
    try:
        abort_modify = User.objects.filter(username=user, first_name=name, email=email).exists() | Profile.objects.filter(user=request.user, mobile=number).exists()
        if abort_modify:
            return Response({'success': 'All parameters are the same'}, status=status.HTTP_200_OK)

        check_number = Profile.objects.filter(mobile=number).exists()
        check_username = User.objects.filter(username=username).exists()
        check_email = User.objects.filter(email=email).exists()
        
        if check_number:
            raise serializers.ValidationError({'error': 'Phone number already exist'})
        elif check_username:
            raise serializers.ValidationError({'error': 'Username already taken'})
        elif check_email:
            raise serializers.ValidationError({'error': 'email is already taken'})
        else:
            user_profile = User.objects.get(username=request.user.username)
            user_profile.first_name = name
            user_profile.email = email
            user_profile.cover_image = cover_image
            user_profile.save()
            user_profile = Profile.objects.get(user=request.user)
            user_profile.cover_image = cover_image
            user_profile.mobile = number
            user_profile.website = website
            user_profile.bio = bio
            user_profile.sex = sex
            user_profile.save()
            return Response({'success': 'Profile updated'}, status=status.HTTP_201_CREATED)
    except:
        return Response({'error' : 'error in handling data'}, status=status.HTTP_400_BAD_REQUEST)
        
        