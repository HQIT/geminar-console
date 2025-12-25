from rest_framework import serializers
from .models import Seminar, GenerationOrder, Voice, Avatar, Speaker, AvatarAction


class SeminarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seminar
        fields = '__all__'


class GenerationOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationOrder
        fields = '__all__'


class VoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voice
        fields = '__all__'


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = '__all__'


class AvatarActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvatarAction
        fields = '__all__'


class AvatarDetailSerializer(serializers.ModelSerializer):
    actions = AvatarActionSerializer(many=True, read_only=True)

    class Meta:
        model = Avatar
        fields = '__all__'


class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = '__all__'

