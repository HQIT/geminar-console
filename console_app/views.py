"""
用户 API - 微课管理、讲师管理等
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from .models import Seminar, Avatar, Speaker, Voice, GenerationOrder
from .serializers import (
    SeminarSerializer, AvatarSerializer, SpeakerSerializer,
    AvatarDetailSerializer, VoiceSerializer, GenerationOrderSerializer
)

import string
import random
import base64
import logging
import requests
import time
import datetime

_logger = logging.getLogger(__name__)


class MyResponse(Response):
    def __init__(self, data=None, code=200, error='', status=None, template_name=None, headers=None, exception=False, content_type=None):
        super().__init__(data, status, template_name, headers, exception, content_type)
        self.data = {'code': code, 'data': data, 'error': error}


class DefaultPagination(PageNumberPagination):
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return MyResponse(data={
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class UserSerializer(serializers.ModelSerializer):
    portrait = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'portrait']

    def get_portrait(self, obj):
        return "./portrait"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me_view(request):
    user = request.user
    # OAuth2 登录检查 token 是否过期
    if 'oauth2_token' in request.session:
        token = request.session['oauth2_token']
        token_expires_at = token.get('expires_at', 0)
        if token_expires_at < time.time():
            return MyResponse(code=401, error=f"token expired", status=status.HTTP_401_UNAUTHORIZED)
    # 本地登录：只要 user 已认证即可

    serializer = UserSerializer(user)
    return MyResponse(data=serializer.data)


@permission_classes([IsAuthenticated])
def get_user_me_portrait(request):
    user = request.user
    access_token = request.session.get('oauth2_token', {}).get('access_token')
    user_photo_url = f"{settings.OAUTH2_USER_PHOTO_URL}?userId={user.username}&access_token={access_token}"
    response = requests.get(user_photo_url)
    if response.status_code != 200:
        return HttpResponse(status=response.status_code)
    content_type = response.headers.get('Content-Type', 'application/unknown')
    return HttpResponse(response.content, content_type=content_type)


def home(request):
    ctx = {'oauth2_token_expired': True}
    if 'oauth2_token' in request.session:
        token = request.session['oauth2_token']
        token_expires_at = token.get('expires_at', 0)
        ctx['oauth2_token_expired'] = token_expires_at < time.time()
    return render(request, 'home.html', ctx)


def logout(request):
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


def oauth2_login(request):
    next_url = request.GET.get('next', '/')
    oauth2_session = OAuth2Session(
        settings.OAUTH2_CLIENT_ID,
        redirect_uri=settings.OAUTH2_REDIRECT_URI
    )
    authorization_url, state = oauth2_session.authorization_url(settings.OAUTH2_AUTHORIZATION_URL)
    request.session['oauth2_state'] = state
    request.session['next_url'] = next_url
    return redirect(authorization_url)


def oauth2_callback(request):
    oauth2_session = OAuth2Session(
        settings.OAUTH2_CLIENT_ID,
        state=request.session['oauth2_state'],
        redirect_uri=settings.OAUTH2_REDIRECT_URI
    )
    token = oauth2_session.fetch_token(
        settings.OAUTH2_TOKEN_URL,
        client_secret=settings.OAUTH2_CLIENT_SECRET,
        authorization_response=request.build_absolute_uri()
    )
    request.session['oauth2_token'] = token

    userinfo = oauth2_session.get(settings.OAUTH2_USERINFO_URL).json()
    userdata = userinfo.get('data', {})
    username = userdata.get('userId')
    firstname = userdata.get('name', 'N/A')
    email = userdata.get('email', '')

    user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'first_name': firstname})
    if not created:
        user.email = email
        user.first_name = firstname
        user.save()

    auth_login(request, user)
    next_url = request.session.pop('next_url', settings.LOGIN_REDIRECT_URL)
    return redirect(next_url)


class SeminarDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, seminar_id):
        try:
            seminar = Seminar.objects.get(id=seminar_id, owner=request.user)
        except Seminar.DoesNotExist:
            return MyResponse(code=404, error="Seminar not exists", status=status.HTTP_404_NOT_FOUND)
        serializer = SeminarSerializer(seminar)
        return MyResponse(data=serializer.data)

    def put(self, request, seminar_id):
        new_state = request.data.get('state', None)
        if new_state not in ['archived', 'draft', None]:
            return MyResponse(code=400, error="only 'archived' or 'draft' allowed", status=status.HTTP_400_BAD_REQUEST)

        seminar = Seminar.objects.get(id=seminar_id, owner=request.user)
        fromto = f"{seminar.state}-{new_state}"
        if new_state and fromto not in ['empty-draft', 'draft-archived']:
            return MyResponse(code=400, error="only 'empty-->draft' or 'draft-->archived' allowed", status=status.HTTP_400_BAD_REQUEST)

        serializer = SeminarSerializer(seminar, data=request.data, partial=True)

        if fromto == 'draft-archived':
            try:
                GenerationOrder.objects.create(seminar=serializer.instance)
            except Exception as e:
                _logger.error(f"创建生成任务失败: {str(e)}", exc_info=True)
                return MyResponse(code=400, error=f"创建生成任务失败 {e}", status=status.HTTP_400_BAD_REQUEST)
            serializer.instance.state = 'pending'

        if serializer.instance.state == 'draft':
            serializer.instance.status.update(dict(step=2))

        if serializer.is_valid():
            serializer.save()
            return MyResponse(data=serializer.data)
        return MyResponse(code=400, error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, seminar_id):
        if not Seminar.objects.filter(id=seminar_id, owner=request.user).exists():
            return MyResponse(code=404, error="Seminar not exists", status=status.HTTP_404_NOT_FOUND)
        seminar = Seminar.objects.get(id=seminar_id, owner=request.user)
        seminar.delete()
        return MyResponse(status=status.HTTP_204_NO_CONTENT)


class SeminarsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get(self, request):
        param_state = request.query_params.get('state', None)
        param_name = request.query_params.get('name', None)
        states = param_state.split(',') if param_state else []
        states = [s.strip() for s in states]

        user = request.user
        query = Q(owner=user)

        if states and not (len(states) == 1 and states[0] in ['all', '全部']):
            query &= Q(state__in=states)

        if param_name and len(param_name.strip()) > 0:
            query &= Q(title__icontains=param_name)

        seminars = Seminar.objects.filter(query).order_by('-date')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(seminars, request)
        if page is not None:
            serializer = SeminarSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        return MyResponse(code=404, error="未找到微课", status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        title = request.data.get('title')
        description = request.data.get('description', '')
        speaker_id = request.data.get('speaker')

        if not title or not speaker_id:
            return MyResponse(code=400, error="title and speaker is required", status=status.HTTP_400_BAD_REQUEST)

        try:
            speaker = Speaker.objects.get(Q(id=speaker_id) & (Q(owner=request.user) | Q(type='system')))
        except Speaker.DoesNotExist:
            return MyResponse(code=400, error=f"speaker {speaker_id} not exists", status=status.HTTP_400_BAD_REQUEST)

        new_seminar = Seminar.objects.create(
            title=title,
            description=description,
            speaker=speaker,
            owner=request.user,
        )
        new_seminar.status = new_seminar.status or {}
        new_seminar.status.update(dict(step=1))
        new_seminar.save()

        serializer = SeminarSerializer(new_seminar)
        return MyResponse(data=serializer.data, status=status.HTTP_201_CREATED)


class AvatarsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get(self, request):
        avatars = Avatar.objects.filter(Q(type='system') | Q(owner=request.user))
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(avatars, request)
        if page is not None:
            serializer = AvatarSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        return MyResponse(code=404, error="未找到头像", status=status.HTTP_404_NOT_FOUND)


class AvatarDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, avatar_id):
        avatar = Avatar.objects.get(id=avatar_id)
        serializer = AvatarDetailSerializer(avatar)
        return MyResponse(data=serializer.data)

    def put(self, request, avatar_id):
        avatar = Avatar.objects.get(id=avatar_id, owner=request.user)
        serializer = AvatarSerializer(avatar, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return MyResponse(data=serializer.data)
        return MyResponse(code=400, error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, avatar_id):
        if not Avatar.objects.filter(id=avatar_id, owner=request.user, type='user').exists():
            return Response({"error": "Avatar not exists"}, status=status.HTTP_404_NOT_FOUND)
        avatar = Avatar.objects.get(id=avatar_id, owner=request.user, type='user')
        avatar.delete()
        return MyResponse(status=status.HTTP_204_NO_CONTENT)


class SpeakerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, speaker_id):
        try:
            speaker = Speaker.objects.get(id=speaker_id, owner=request.user)
        except Speaker.DoesNotExist:
            return MyResponse(code=404, error="Speaker not exists", status=status.HTTP_404_NOT_FOUND)
        serializer = SpeakerSerializer(speaker)
        return MyResponse(data=serializer.data)

    def put(self, request, speaker_id):
        speaker = Speaker.objects.get(id=speaker_id, owner=request.user)
        serializer = SpeakerSerializer(speaker, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return MyResponse(data=serializer.data)
        return MyResponse(code=400, error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, speaker_id):
        if not Speaker.objects.filter(id=speaker_id, owner=request.user, type='user').exists():
            return MyResponse(code=404, error="Speaker not exists", status=status.HTTP_404_NOT_FOUND)
        speaker = Speaker.objects.get(id=speaker_id, owner=request.user, type='user')
        speaker.delete()
        return MyResponse(status=status.HTTP_204_NO_CONTENT)


class SpeakersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get(self, request):
        speakers = Speaker.objects.filter(Q(type='system') | Q(owner=request.user))
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(speakers, request)
        if page is not None:
            serializer = SpeakerSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        return MyResponse(code=404, error="未找到讲师", status=status.HTTP_404_NOT_FOUND)

    def _verify_face(self, new_photo, user_avatar):
        client = BackendApplicationClient(client_id=settings.OAUTH2_CLIENT_ID)
        session = OAuth2Session(client=client)
        token = session.fetch_token(
            token_url=settings.OAUTH2_TOKEN_URL,
            client_secret=settings.OAUTH2_CLIENT_SECRET,
            include_client_id=True
        )
        headers = {'Content-Type': 'application/json'}
        data = {'image1': new_photo, 'image2': user_avatar}
        response = session.post(url=settings.OAUTH2_FACE_COMPARE_URL, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            confidence = result['data']['confidence']
            thresholds = result['data']['thresholds']
            if confidence >= thresholds['1e-4']:
                return True
        return False

    def post(self, request):
        portrait = request.FILES.get('portrait')
        if not portrait:
            return MyResponse(code=400, error="未提供照片", status=status.HTTP_400_BAD_REQUEST)
        portrait_content = portrait.read()

        user_photo_url = f"{settings.OAUTH2_USER_PHOTO_URL}?userId={request.user.username}"
        oauth2_session = OAuth2Session(settings.OAUTH2_CLIENT_ID, token=request.session.get('oauth2_token'))
        response = oauth2_session.get(user_photo_url)
        if response.status_code != 200:
            return MyResponse(code=400, error=f"获取用户头像失败", status=status.HTTP_400_BAD_REQUEST)

        user_avatar = response.content
        if not user_avatar:
            return MyResponse(code=400, error="用户没有头像", status=status.HTTP_400_BAD_REQUEST)

        encoded_portrait = base64.b64encode(portrait_content).decode('utf-8')
        encoded_user_avatar = base64.b64encode(user_avatar).decode('utf-8')
        if not self._verify_face(encoded_portrait, encoded_user_avatar):
            return MyResponse(code=400, error="人脸验证失败", status=status.HTTP_400_BAD_REQUEST)

        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        new_avatar = Avatar.objects.create(
            name=f"{request.user.username}-{random_suffix}",
            portrait=portrait,
            owner=request.user
        )

        voice_id = request.POST.get('voice', None)
        if not voice_id:
            return MyResponse(code=400, error="未提供声音", status=status.HTTP_400_BAD_REQUEST)
        voice = Voice.objects.get(id=voice_id)

        new_speaker = Speaker.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            avatar=new_avatar,
            voice=voice,
            owner=request.user
        )

        serializer = SpeakerSerializer(new_speaker)
        return MyResponse(data=serializer.data, status=status.HTTP_201_CREATED)


class VoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        voices = Voice.objects.all()
        serializer = VoiceSerializer(voices, many=True)
        return MyResponse(data=serializer.data)


class GenerationOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        seminar_id = request.data.get('seminar', None)
        if not Seminar.objects.filter(id=seminar_id).exists():
            return MyResponse(code=400, error="微课不存在", status=status.HTTP_400_BAD_REQUEST)
        seminar = Seminar.objects.get(id=seminar_id)

        if GenerationOrder.objects.filter(seminar=seminar).exists():
            return MyResponse(code=400, error="微课生成任务已存在", status=status.HTTP_400_BAD_REQUEST)

        generation_order = GenerationOrder.objects.create(seminar=seminar)
        serializer = GenerationOrderSerializer(generation_order)
        return MyResponse(data=serializer.data)

