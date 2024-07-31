
from django.urls import path
from .views import my_view , PromptAPIView , WhatsAppMessageView

urlpatterns = [
    path('', my_view, name='my_view'),
    path('api/prompt', PromptAPIView.as_view(), name='prompt_api'),
    path('whatsapp/', WhatsAppMessageView.as_view(), name='whatsapp-message'),
    # path('bot/chat/', ChatAPIView.as_view(), name='chat_api'),
    # path('bot/send-mail/', SendMailView.as_view(), name='send_mail'),
]
