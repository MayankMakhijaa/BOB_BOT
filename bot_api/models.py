from django.db import models
from langchain.schema import SystemMessage, AIMessage, HumanMessage

# Create your models here.
class Chat(models.Model):
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question} | {self.timestamp}"

class WhatsAppChatHistory(models.Model):
    phone_number = models.CharField(max_length=20)
    messages = models.JSONField(default=list)  # Storing chat history as a JSON array
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {self.timestamp}"

    def get_messages(self):
        # Deserialize JSON messages into LangChain message objects
        return [self.deserialize_message(msg) for msg in self.messages]

    def set_messages(self, messages):
        # Serialize LangChain message objects into JSON-serializable dictionaries
        self.messages = [self.serialize_message(msg) for msg in messages]

    @staticmethod
    def serialize_message(message):
        if isinstance(message, SystemMessage):
            return {'role': 'system', 'content': message.content}
        elif isinstance(message, AIMessage):
            return {'role': 'assistant', 'content': message.content}
        elif isinstance(message, HumanMessage):
            return {'role': 'user', 'content': message.content}
        else:
            raise ValueError(f"Unknown message type: {type(message)}")

    @staticmethod
    def deserialize_message(message):
        role = message['role']
        content = message['content']
        if role == 'system':
            return SystemMessage(content=content)
        elif role == 'assistant':
            return AIMessage(content=content)
        elif role == 'user':
            return HumanMessage(content=content)
        else:
            raise ValueError(f"Unknown message role: {role}")