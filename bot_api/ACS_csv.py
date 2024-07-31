import csv
import json
import asyncio
import time
import urllib
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, SearchableField,
    VectorSearch, HnswAlgorithmConfiguration, HnswParameters,
    VectorSearchAlgorithmKind, VectorSearchAlgorithmMetric, VectorSearchProfile,
    SemanticConfiguration, SemanticPrioritizedFields, SemanticField,
    ExhaustiveKnnAlgorithmConfiguration, ExhaustiveKnnParameters
)
from openai import AzureOpenAI
import os
import concurrent.futures
from azure.search.documents.indexes.models import SemanticSearch
# Load environment variables
load_dotenv()
AZURE_COGNITIVE_SEARCH_ENDPOINT = os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT")
AZURE_COGNITIVE_SEARCH_API_KEY = os.getenv("AZURE_COGNITIVE_SEARCH_API_KEY")
AZURE_COGNITIVE_SEARCH_INDEX_NAME = os.getenv("AZURE_COGNITIVE_SEARCH_INDEX_NAME")


CSV_FILE_PATH = 'data_token_21_3_24.csv'
JSON_FILE_PATH = 'data_token_21_3_24.json'
EMBEDDING_LENGTH = 3072
COGSEARCH_INDEX_NAME = 'bob_index_0'

# Initialize Azure OpenAI client
# aoai_client = AzureOpenAI(
#     api_key=config['openai_api_key'],
#     azure_endpoint=config['openai_api_endpoint'],
#     api_version=config['openai_api_version']
# )
openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai_api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_version = "2024-03-01-preview"
openai_deployment_embedding = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")

# Initialize Azure OpenAI client
aoai_client = AzureOpenAI(api_key=openai_api_key, azure_endpoint=openai_api_base, api_version=openai_api_version)

def csv_to_json(csv_file_path, json_file_path):
    data = []
    with open(csv_file_path, 'r', encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            data.append(row)
    with open(json_file_path, 'w', encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)


def retry_with_backoff(retries=5, backoff_in_seconds=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            x = backoff_in_seconds
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        raise
                    else:
                        print(f"Retry {i + 1}/{retries} after {x} seconds due to error: {e}")
                        time.sleep(x)
                        x *= 2
        return wrapper
    return decorator

@retry_with_backoff()   
def generate_embeddings(text):
    lower_text = text.lower()
    response = aoai_client.embeddings.create(input=lower_text, model=openai_deployment_embedding)
    embeddings = response.model_dump()
    return embeddings['data'][0]['embedding']

def process_item(item):
    try:
        title = item['title']
        content = item['content']
        item['titleVector'] = generate_embeddings(title)
        item['contentVector'] = generate_embeddings(content)
        item['@search.action'] = 'upload'
    except Exception as e:
        print(f"Error processing item: {e}")
    return item

def process_data(data):
    counter = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = []
        for result in executor.map(process_item, data):
            results.append(result)
            counter += 1
            if counter % 100 == 0:
                print(f"Processed {counter} items, sleeping for 5 seconds...")
                time.sleep(20)  # Sleep for 5 seconds after every 100 requests
    return results

def create_search_index(index_name):
    credential = AzureKeyCredential(AZURE_COGNITIVE_SEARCH_API_KEY)
    index_client = SearchIndexClient(endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT, credential=credential)

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
        SearchableField(name="title", type=SearchFieldDataType.String, filterable=True, searchable=True, allowUnsafeKeys=True),
        SearchableField(name="content", type=SearchFieldDataType.String, filterable=True, searchable=True, allowUnsafeKeys=True),
        SearchField(name="titleVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, vector_search_dimensions=EMBEDDING_LENGTH, vector_search_profile_name="myHnswProfile"),
        SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, vector_search_dimensions=EMBEDDING_LENGTH, vector_search_profile_name="myHnswProfile"),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters=HnswParameters(
                    m=4,
                    ef_construction=400,
                    ef_search=500,
                    metric=VectorSearchAlgorithmMetric.COSINE
                )
            ),
            ExhaustiveKnnAlgorithmConfiguration(
                name="myExhaustiveKnn",
                kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                parameters=ExhaustiveKnnParameters(
                    metric=VectorSearchAlgorithmMetric.COSINE
                )
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            ),
            VectorSearchProfile(
                name="myExhaustiveKnnProfile",
                algorithm_configuration_name="myExhaustiveKnn",
            )
        ]
    )

    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            keywords_fields=[SemanticField(field_name="title")],
            content_fields=[SemanticField(field_name="content")],
        )
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search)
    result = index_client.create_or_update_index(index)
    print(f'{result.name} created')

def upload_documents(documents):
    chunk_size = 100
    num_documents = len(documents)
    num_chunks = (num_documents + chunk_size - 1) // chunk_size
    
    print(f"Uploading {num_documents} documents in {num_chunks} chunks...")
    
    search_client = SearchClient(
        endpoint=AZURE_COGNITIVE_SEARCH_ENDPOINT,
        index_name=COGSEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_COGNITIVE_SEARCH_API_KEY)
    )
    
    results = []
    
   
    for i in range(num_chunks):
        start_index = i * chunk_size
        end_index = min((i + 1) * chunk_size, num_documents)
        chunk = documents[start_index:end_index]
        
        print(f"Uploading chunk {i+1}/{num_chunks}...{start_index}:{end_index}")

        result = search_client.upload_documents(documents=chunk)
        time.sleep(20)
        results.append(result)
        
    return results

    
    return results

def main():
    # csv_to_json(CSV_FILE_PATH, JSON_FILE_PATH)

    # with open(JSON_FILE_PATH, 'r') as file:
    with open("D:\\BoB_api\\processed_data.json", "r") as file:
        data = json.load(file)

    # # Process data and generate embeddings
    # data = process_data(data)

    # Save processed data to JSON file
    # with open("processed_data.json", "w") as f:
    #     json.dump(data, f)

    # Create Azure Cognitive Search index
    create_search_index(COGSEARCH_INDEX_NAME)

    # Upload documents to Azure Cognitive Search
    result = upload_documents(data)
    print(f"Documents uploaded: {result}")

if __name__ == "__main__":
    main()
