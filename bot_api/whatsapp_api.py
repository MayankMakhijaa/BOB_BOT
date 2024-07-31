# views.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
import openai

# Set up your OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

# Set up your WhatsApp Business API credentials
WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
WHATSAPP_URL = f'https://graph.facebook.com/v12.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if data['object'] == 'whatsapp_business_account':
            for entry in data['entry']:
                for change in entry['changes']:
                    if change['field'] == 'messages':
                        for message in change['value']['messages']:
                            if message['type'] == 'text':
                                phone_number = message['from']
                                question = message['text']['body']

                                # Generate response using OpenAI
                                

                                # Send response back to WhatsApp
                                send_whatsapp_message(phone_number, response)

        return HttpResponse('OK', status=200)
    else:
        return HttpResponse('Method not allowed', status=405)


def generate_openai_response(question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message['content']


def send_whatsapp_message(phone_number, message):
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        'messaging_product': 'whatsapp',
        'to': phone_number,
        'type': 'text',
        'text': {'body': message}
    }

    response = requests.post(WHATSAPP_URL, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {response.text}")


# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
]

# settings.py
OPENAI_API_KEY = 'your_openai_api_key'
WHATSAPP_TOKEN = 'your_whatsapp_token'
WHATSAPP_PHONE_NUMBER_ID = 'your_phone_number_id'