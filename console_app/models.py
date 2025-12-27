"""
数据模型 - 共享数据库访问
managed = False，不负责创建/修改数据库表
数据库表由 geminar-admin 管理
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

import os
import hashlib
import uuid


class ResourceType(models.TextChoices):
    SYSTEM = 'system', 'System'
    USER = 'user', 'User'


class Voice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=100, default=uuid.uuid4)
    description = models.TextField()
    sample = models.FileField(upload_to='voices/')

    class Meta:
        managed = False
        db_table = 'api_voice'

    def __str__(self):
        return self.title


def _default_motions():
    return dict(silent='', talking='')


def _default_covers():
    return dict(_16x9="", _4x3="")


def _avatar_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    md5_name = hashlib.md5(filename.encode()).hexdigest()
    return os.path.join('avatars', instance.owner.username, f'{md5_name}{ext}')


class Avatar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    portrait = models.ImageField(upload_to=_avatar_upload_path)
    description = models.TextField(default='')
    type = models.CharField(max_length=10, choices=ResourceType.choices, default=ResourceType.USER)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avatars', default=1)
    motions = models.JSONField(default=_default_motions)

    class Meta:
        managed = False
        db_table = 'api_avatar'

    def __str__(self):
        return self.name


class AvatarAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, default='silent')
    description = models.TextField(default='')
    avatar = models.ForeignKey(Avatar, on_delete=models.CASCADE, related_name='actions')

    class Meta:
        managed = False
        db_table = 'api_avataraction'


class Speaker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    avatar = models.ForeignKey(Avatar, on_delete=models.CASCADE, related_name='speakers', null=True, blank=True)
    voice = models.ForeignKey(Voice, on_delete=models.CASCADE, related_name='speakers', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='speakers', default=1)
    type = models.CharField(max_length=10, choices=ResourceType.choices, default=ResourceType.USER)
    motions = models.JSONField(default=_default_motions)
    covers = models.JSONField(default=_default_covers)

    class Meta:
        managed = False
        db_table = 'api_speaker'

    def __str__(self):
        return self.name


def _default_status():
    return dict(progress=0, queuing=0, step=0)


def _default_resources():
    return dict(slides=[])


class Seminar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seminars', default=1)
    state = models.CharField(max_length=50, default='empty')
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE, related_name='seminars', null=True, blank=True)
    cover = models.TextField(null=True, blank=True)
    status = models.JSONField(default=_default_status)
    resources = models.JSONField(default=_default_resources)

    class Meta:
        managed = False
        db_table = 'api_seminar'

    def __str__(self):
        return self.title


def _default_generation_status():
    return dict(description='')


class GenerationOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=50, default='pending')
    status = models.JSONField(default=_default_generation_status)
    created_at = models.DateTimeField(auto_now_add=True)
    seminar = models.ForeignKey(Seminar, on_delete=models.CASCADE, related_name='orders')

    class Meta:
        managed = False
        db_table = 'api_generationorder'

    def __str__(self):
        return str(self.id)


def _default_tts_status():
    return dict(progress=0, error='')


class TTSOrderState(models.TextChoices):
    PENDING = 'pending', _('等待处理')
    HANDLING = 'handling', _('处理中')
    COMPLETED = 'completed', _('已完成')
    FAILED = 'failed', _('失败')


class TTSOrder(models.Model):
    """TTS 转换任务"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(verbose_name='待转换文本')
    spk_id = models.CharField(max_length=100, verbose_name='音色 ID')
    state = models.CharField(
        max_length=20,
        choices=TTSOrderState.choices,
        default=TTSOrderState.PENDING,
        verbose_name='状态'
    )
    status = models.JSONField(default=_default_tts_status, verbose_name='状态详情')
    output_file = models.CharField(max_length=500, blank=True, verbose_name='输出文件路径')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tts_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True  # 由 console 管理
        db_table = 'console_ttsorder'
        ordering = ['-created_at']

    def __str__(self):
        return f"TTS-{self.id}"

