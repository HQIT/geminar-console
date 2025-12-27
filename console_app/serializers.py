from rest_framework import serializers
from .models import Seminar, GenerationOrder, Voice, Avatar, Speaker, AvatarAction, TTSOrder


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


class TTSOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TTSOrder
        fields = '__all__'
        read_only_fields = ['id', 'state', 'status', 'output_file', 'owner', 'created_at', 'updated_at']


class TTSOrderCreateSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    spk_id = serializers.CharField(required=True)

