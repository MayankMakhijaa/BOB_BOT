from django.shortcuts import render
from .serializers import ChatSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from .stream_structure_agent import myBOBBot
from .stream_structure_agent1 import BOBWhatsappBot
from django.http import StreamingHttpResponse
from rest_framework import status
import datetime
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.timezone import now
import asyncio
import json
from json.decoder import JSONDecodeError
import uuid
from langchain_core.messages import HumanMessage, SystemMessage ,AIMessage
from .models import WhatsAppChatHistory
from .serializers import WhatsAppChatHistorySerializer

# Create your views here.
def my_view(request):
    return render(request, "index.html")


def generate_user_id():
        return str(uuid.uuid4())

def iter_over_async(ait, loop):
    ait = ait.__aiter__()
    async def get_next():
        try: obj = await ait.__anext__(); return False, obj
        except StopAsyncIteration: return True, None
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done: break
        yield obj
# Dictionary to store chat history
chat_history = {}
class PromptAPIView(APIView):
    
    def post(self, request, *args, **kwargs):
        if 'user_id' not in request.session:
            request.session['user_id'] = generate_user_id()
            request.session['last_activity'] = datetime.datetime.now().isoformat()

        session_id = request.session['user_id']
        if session_id not in chat_history:
            chat_history[session_id] = []
        print(chat_history)

        try:
            data = json.loads(request.body)
            prompt = data['prompt']
            chunks = []
        except JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON: {e}"}, status=400)

        # Pass context to myBOBBot instance
        ob1 = myBOBBot(chat_history[session_id])
        

        def generate():
            try:
                if len(ob1.message) == 0:
                    with open("prompts/main_prompt.txt", "r", encoding="utf-8") as f:
                        text = f.read()
                    ob1.message.append(SystemMessage(content=f"{text}"))
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                openairesponse = iter_over_async(ob1.run_conversation(prompt), loop)
                # openairesponse = ob1.run_conversation(prompt)
                # Yield response
                for event in openairesponse:
                    kind = event["event"]
                    if kind == "on_chain_start":
                        if event["name"] == "Agent":
                            print(f"Starting agent: {event['name']} with input: {event['data'].get('input')}")
                    elif kind == "on_chain_end":
                        if event["name"] == "Agent":
                            print()
                            print("--")
                            print(f"Done agent: {event['name']} with output: {event['data'].get('output')['output']}")
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            print(content, end="|")
                            chunks.append(content)
                            yield content
                    elif kind == "on_tool_start":
                        print("--")
                        print(f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}")
                    elif kind == "on_tool_end":
                        print(f"Done tool: {event['name']}")
                        print(f"Tool output was: {event['data'].get('output')}")
                        print("--")
                    # return Response({'responce': f"{chunks}"})
                answer = "".join(chunks)
                ob1.message.append(AIMessage(content=f"{answer}"))
                chat_history[session_id] = ob1.message

            except Exception as e:
                yield JsonResponse({"error": str(e)}, status=500)

        return StreamingHttpResponse(generate(), content_type="application/json")


class WhatsAppMessageView(APIView):
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        message = request.data.get('message')
        
        # Fetch or create chat history
        chat_history, created = WhatsAppChatHistory.objects.get_or_create(phone_number=phone_number)
        
        if created:
            chat_history.messages = []
        
        # Append the new message
        # chat_history.messages.append({'role': 'user', 'content': message})

        # Initialize the bot with chat history
        messages = chat_history.get_messages()
        ob1 = BOBWhatsappBot(messages)
        
        def generate():
            try:
                # Read the system prompt if no messages exist
                if len(ob1.message) == 0:
                    with open("prompts/main_prompt.txt", "r", encoding="utf-8") as f:
                        text = f.read()
                    ob1.message.append(SystemMessage(content=f"{text}"))
                
                # Generate the response
                response = ob1.run_conversation(message)
                
                # Extract and append the response
                answer = response
                ob1.message.append(AIMessage(content=f"{answer}"))
                print(answer)
                # Send response back to WhatsApp
                # self.send_message_to_whatsapp(phone_number, answer)
                # Save the updated chat history
                # chat_history.messages = ob1.message
                chat_history.set_messages(ob1.message)
                chat_history.save()
                return answer
                # return Response({'answer': answer}, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"Error in generate function: {e}")
                return Response({'error': e}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'answer': generate()}, status=status.HTTP_200_OK)

        

        

    def send_message_to_whatsapp(self, phone_number, message):
        url = 'https://api.whatsapp.com/send'  # Replace with actual WhatsApp API URL
        headers = {
            'Authorization': 'Bearer your-whatsapp-api-token',
            'Content-Type': 'application/json'
        }
        payload = {
            'phone': phone_number,
            'message': message
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            # Handle the error appropriately
            print(f"Failed to send message: {response.text}")

