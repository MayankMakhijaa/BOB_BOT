from rest_framework import serializers
from .models import  Chat , WhatsAppChatHistory


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'
        extra_kwargs = {
            'answer': {'required': False}  # Make answer field optional
        }
        
class WhatsAppChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppChatHistory
        fields = '__all__'
        extra_kwargs = {
            'answer': {'required': False}  # Make answer field optional
        }

