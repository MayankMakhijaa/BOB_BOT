import json
import os

import tiktoken
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType
from dotenv import load_dotenv
from openai import AzureOpenAI
from json import JSONDecodeError
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_react_agent, Tool, create_openai_functions_agent
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.agents import Agent, load_tools, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
import asyncio
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.tools import StructuredTool    
# from pydantic.v1 import BaseModel, Field
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import AgentExecutor
from langchain_core.runnables import RunnablePassthrough
from langchain_community.callbacks import get_openai_callback
load_dotenv()

class BOBWhatsappBot:
    is_function_calling = 0

    def __init__(self,message):
        self.API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.RESOURCE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.client = AzureChatOpenAI(api_key=self.API_KEY, api_version="2023-07-01-preview",
                                      azure_endpoint=self.RESOURCE_ENDPOINT, azure_deployment="BoBGPT4o" )
        self.Completion_Model = os.getenv("AZURE_OPENAI_COMPLETION_MODEL")
        # print(self.Completion_Model)
        self.folder_path = 'Prompts'
        self.session_id = ""
        self.message = message
        self.AZURE_COGNITIVE_SEARCH_ENDPOINT = os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT")
        self.AZURE_COGNITIVE_SEARCH_API_KEY = os.getenv("AZURE_COGNITIVE_SEARCH_API_KEY")
        self.AZURE_COGNITIVE_SEARCH_INDEX_NAME = os.getenv("AZURE_COGNITIVE_SEARCH_INDEX_NAME")
        self.ENCODING = "cl100k_base"
        self.search_client = SearchClient(endpoint=self.AZURE_COGNITIVE_SEARCH_ENDPOINT,
                                          index_name=self.AZURE_COGNITIVE_SEARCH_INDEX_NAME,
                                          credential=AzureKeyCredential(self.AZURE_COGNITIVE_SEARCH_API_KEY))
        self.user_input = ""
        self.store = {}

    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    # @tool(infer_schema=False)
    # def open_saving_account(*args, **kwargs):
    #     """Provide Information when user wants to open a saving account"""
    #     if BOBWhatsappBot.is_function_calling != 8:
    #         print("Open saving account function called")
    #         with open("prompts/saving_accounts.txt", "r", encoding="utf-8") as f:
    #             text = f.read()
    #         ob1.message.clear()
    #         ob1.message.append(SystemMessage(content=f"{text}"))
    #         ob1.message.append(HumanMessage(content=ob1.user_input))
    #         BOBWhatsappBot.is_function_calling = 8
    # @tool(infer_schema=False)
    def open_saving_account(self,*args, **kwargs):
        """Provide Information when user wants to open a saving account"""
        if BOBWhatsappBot.is_function_calling != 8:
            print("Open saving account function called")
            with open("prompts/saving_accounts.txt", "r", encoding="utf-8") as f:
                text = f.read()
            # if self.session_id not in self.store:
            self.store[self.session_id] = ChatMessageHistory(messages=self.message).clear()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            self.store[self.session_id] = ChatMessageHistory(messages=self.message)
            BOBWhatsappBot.is_function_calling = 8

    # @tool(infer_schema=False)
    # def open_current_account(*args, **kwargs):
    #     """Provide Information when user wants to open a current account"""
    #     if BOBWhatsappBot.is_function_calling != 1:
    #         print("Open current account function called")
    #         with open("prompts/current_account.txt", "r", encoding="utf-8") as f:
    #             text = f.read()
    #         ob1.message.clear()
    #         ob1.message.append(SystemMessage(content=f"{text}"))
    #         ob1.message.append(HumanMessage(content=ob1.user_input))
    #         BOBWhatsappBot.is_function_calling = 1
    
    # @tool(infer_schema=False)
    def open_current_account(self,*args, **kwargs):
        """Provide Information when user wants to open a current account"""
        if BOBWhatsappBot.is_function_calling != 1:
            print("Open current account function called")
            with open("prompts/current_account.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 1

    
    def open_government_account(self,*args, **kwargs):
        """Provide Information when user wants to open a government account"""
        if BOBWhatsappBot.is_function_calling != 2:
            print("Open government account function called")
            with open("prompts/government.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 2

    
    def get_home_loan(self,*args, **kwargs):
        """Provide Information when user wants to get a home loan"""
        if BOBWhatsappBot.is_function_calling != 3:
            print("Get home loan function called")
            with open("prompts/home_loan.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 3

    
    def open_insurance_account(self,*args, **kwargs):
        """Provide Information when user wants to open an insurance account"""
        if BOBWhatsappBot.is_function_calling != 4:
            print("Open insurance account function called")
            with open("prompts/insurance.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 4

    
    def open_locker_account(self,*args, **kwargs):
        """Provide Information when user wants to open a locker account"""
        if BOBWhatsappBot.is_function_calling != 5:
            print("Open locker account function called")
            with open("prompts/locker.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 5

    
    def open_nri_account(self,*args, **kwargs):
        """Provide Information when user wants to open an NRI account"""
        if BOBWhatsappBot.is_function_calling != 6:
            print("Open NRI account function called")
            with open("prompts/nri.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 6

    
    def get_personal_loan(self,*args, **kwargs):
        """Provide Information when user wants to get a personal loan"""
        if BOBWhatsappBot.is_function_calling != 7:
            print("Get personal loan function called")
            with open("prompts/personal_loan.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 7

    
    def open_term_deposit_account(self,*args, **kwargs):
        """Provide Information when user wants to open a term deposit account"""
        if BOBWhatsappBot.is_function_calling != 9:
            print("Open term deposit account function called")
            with open("prompts/term_deposit.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 9

    
    def get_vehicle_loan(self,*args, **kwargs):
        """Provide Information when user wants to get a vehicle loan"""
        if BOBWhatsappBot.is_function_calling != 10:
            print("Get vehicle loan function called")
            with open("prompts/vehicle_loan.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 10

    
    def open_wms_account(self,*args, **kwargs):
        """Provide Information when user wants to open a WMS account"""
        if BOBWhatsappBot.is_function_calling != 11:
            print("Open WMS account function called")
            with open("prompts/wms.txt", "r", encoding="utf-8") as f:
                text = f.read()
            self.message.clear()
            self.message.append(SystemMessage(content=f"{text}"))
            self.message.append(HumanMessage(content=self.user_input))
            BOBWhatsappBot.is_function_calling = 11

   
    def all_BoB_information(self,user_input,*args, **kwargs):
        """Provide comprehensive information on all services, accounts, loans, schemas, yojanas etc., offered by Bank of Baroda."""
        print("Rag function called ")
        question = user_input
        # question = self.user_input
        max_tokens = 6000
        token_threshold = 0.8 * max_tokens  # 90% of max_tokens as threshold
        print(token_threshold)
        results = self.search_client.search(search_text=question, select=["content", "title"],
                                           # Include 'token' in the select query
                                           query_type=QueryType.SEMANTIC,
                                           semantic_configuration_name='my-semantic-config',
                                           query_caption=QueryCaptionType.EXTRACTIVE,
                                           query_answer=QueryAnswerType.EXTRACTIVE, top=4)

        context = ""
        total_tokens = 0
        num_results = 0

        for result in results:
            title = result['title']
            content = result['content']
            result_tokens = self.num_tokens_from_string(context, self.ENCODING)
            print(result_tokens)
            # Check if adding this result exceeds the token limit
            if total_tokens + result_tokens > token_threshold:
                excess_tokens = total_tokens + result_tokens - token_threshold
                # Reduce the length of the context by truncating it
                context = context[:-int(excess_tokens)]
                break

            # Add this result to context
            print(title)
            context += f"Title: {title}\n Content: {content}\n"
            total_tokens += result_tokens
            num_results += 1

        if BOBWhatsappBot.is_function_calling != 12:
            # with open("prompts/rag_prompt.txt", 'r') as file:
            with open("prompts/main_prompt.txt", 'r') as file:
                header = file.read()
                BOBWhatsappBot.is_function_calling = 12

        # Replace the placeholder "{question}" in the header with the actual question
            header = f'''{header}
            Context : {context}
            Question : {question}
             '''
            # print(header)
            self.message.clear()
            self.message.append(SystemMessage(content=f"{header}"))
            # self.message.append({"role": "system", "content": f"{header}"})
            # self.message.append({"role": "user", "content": self.user_input})
            # self.message = [SystemMessage(content=f"{header}")]

    def run_conversation(self, user_input):
        self.user_input = user_input
        self.message.append(HumanMessage(content=user_input))

        # Initialize the tools
        tools = [
            StructuredTool.from_function(
                func=self.open_saving_account,
                description="Function to provide information when user wants to open a saving account only",
            ),
            StructuredTool.from_function(
                func=self.open_current_account,
                description="Function to provide information when user wants to open a current account only",
            ),
            StructuredTool.from_function(
                func=self.open_government_account,
                description="Function to provide information when user wants to open a government account only",
            ),
            StructuredTool.from_function(
                func=self.get_home_loan,
                description="Function to provide information when user wants to get a home loan only",
            ),
            StructuredTool.from_function(
                func=self.open_insurance_account,
                description="Function to provide information when user wants to open an insurance account only",
            ),
            StructuredTool.from_function(
                func=self.open_locker_account,
                description="Function to provide information when user wants to open a locker account only",
            ),
            StructuredTool.from_function(
                func=self.get_vehicle_loan,
                description="Function to provide information when user wants to get a vehicle loan only",
            ),
            StructuredTool.from_function(
                func=self.open_nri_account,
                description="Function to provide information when user wants to open an NRI account only",
            ),
            StructuredTool.from_function(
                func=self.get_personal_loan,
                description="Function to provide information when user wants to get a personal loan",
            ),
            StructuredTool.from_function(
                func=self.open_term_deposit_account,
                description="Function to provide information when user wants to open a term deposit account",
            ),
            StructuredTool.from_function(
                func=self.open_wms_account,
                description="Function to provide information when user wants to open a WMS account",
            ),
            # StructuredTool.from_function(
            #     func=self.all_BoB_information,
            #     description="Function to provide information on all services, accounts, loans, schemes, yojanas, etc., offered by Bank of Baroda",
            # ),
            StructuredTool.from_function(
                func=self.all_BoB_information,
                description="Tool to provide comprehensive information on a wide range of services,credit cards, loans, schemes, yojanas, and other offerings provided by Bank of Baroda. This tool does not cover account opening details."
            ),
        ]

        llm_with_tools = self.client.bind_tools(tools)

        MEMORY_KEY = "chat_history"
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a very powerful Bank of Baroda assistant.Your role is to choose which tool/agent is suitable for response this user query"),
                MessagesPlaceholder(variable_name=MEMORY_KEY),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        max_response_tokens = 250
        token_limit = 8000
        # Helper function to calculate total tokens in the messages
        def calculate_token_length(messages):
            tokens_per_message = 3
            tokens_per_name = 1
            # encoding = tiktoken.get_encoding(self.ENCODING)
            encoding = tiktoken.encoding_for_model("gpt-4-0613")
            num_tokens = 0
            print(len(messages))
            for message in messages:
                print(message.content)
                num_tokens += tokens_per_message
                # for value in message.content:
                #     print(value)
                num_tokens += len(encoding.encode(message.content))
                    # if key == "name":
                    #     num_tokens += tokens_per_name
            num_tokens += 3 
            print(num_tokens) # every reply is primed with <|start|>assistant<|message|>
            return num_tokens

        # Helper function to ensure message length is within limits
        def ensure_message_length_within_limit(message):
            # print("Lenth Function Called",messages[0])
            messages = self.message
            conv_history_tokens = calculate_token_length(self.message)
            
            while conv_history_tokens + max_response_tokens >= token_limit:
                print("Conv History", conv_history_tokens)
                if len(self.message) > 1:
                    del self.message[1]  # Remove the oldest message
                    conv_history_tokens = calculate_token_length(self.message)
        with get_openai_callback() as cb:
            try:
                
                ensure_message_length_within_limit(self.message)  # Reserve some tokens for functions and overhead
                # for chunk in agent_executor.astream_events(
                #     {"input": user_input, "chat_history": self.message}, version="v1"
                # ):
                #     yield chunk
                response = agent_executor.invoke({"input": user_input, "chat_history": self.message})
                
                return response["output"]

            except Exception as e:
                error_message = f"An error occurred: {e}"
                print(error_message)
                return error_message
            print("Token : ",cb)


                
# def iter_over_async(ait, loop):
#     ait = ait.__aiter__()
#     async def get_next():
#         try: obj = await ait.__anext__(); return False, obj
#         except StopAsyncIteration: return True, None
#     while True:
#         done, obj = loop.run_until_complete(get_next())
#         if done: break
#         yield obj        

# ob1 = BOBWhatsappBot()
# while True:
#     if len(ob1.message) == 0:
#         with open("prompts\main_prompt.txt", "r", encoding="utf-8") as f:
#             text = f.read()
#         ob1.message.append(SystemMessage(content=f"{text}"))
            

#     question = input("Please Enter a Query: ")
#     if question == "end":
#         break

#     openapiresponse = ob1.run_conversation(question)
#     print(openapiresponse)
        

#     ob1.message.append(AIMessage(content=f"{openapiresponse}"))
#     # print(ob1.message)


