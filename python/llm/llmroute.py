import requests
from common.text import unmark
import json

CHUNK_SIZE = 1024
OVERLAP_SIZE = 200

API_URLS = {
    'chat'      : 'http://localhost:11434/api/chat',
    'generate'  : 'http://localhost:11434/api/generate',
    'embeddings': 'http://localhost:11434/api/embeddings',
    # 추가 엔드포인트가 생길 경우 여기에 추가
    # 'another_api': 'http://localhost:11434/api/another'
}


"""
Count Tokens
"""
def count_tokens(text) -> int:
    return count_tokens_ollama(text)

def count_tokens_ollama(text) -> int:
    return -1


"""
Embedding
"""
def embedd_text(text) -> list[float]:
    results = []
    results.extend(embedd_text_ollama(text))
    return results


def embedd_text_ollama(text) -> list[float]:
    api_url = API_URLS['embeddings']
    data = build_request_data(query=text, chunk='', api_type='embeddings')
    response = send_post_request(api_url, data)
    #print(response.json())
    print(text)
    return response.json()['embedding']


"""
Query (chat, completion, instruct, generate, etc)
"""
def query_with_context(query, context) -> list[dict]:
    response_list = query_ollama_with_context(query, context, api_type='generate')
    return response_list
#   query_ollama_with_context(query, context, api_type='chat')
#   query_ollama_with_context(query, context, api_type='another_api')


def query_ollama_with_context(query, context, api_type='chat') -> list[dict]:
    if api_type not in API_URLS:
        raise ValueError(f"Unsupported API type: {api_type}")
    
    api_url = API_URLS[api_type]
    context_chunks = chunking_context(context)
    response_list = []
    
    for chunk in context_chunks:
        data = build_request_data(query, chunk, api_type)
        response = send_post_request(api_url, data)
        try:
            if response:
                ascii_contents = json.loads(parse_response(response, api_type))
                print(f"{response.status_code} {'OK' if response.status_code == 200 else 'NG'}\n{ascii_contents}\n\n")
                response_list.append(ascii_contents)
        except Exception as e:
            print(f"Error during response parsing: {e}")
            continue

    print('> query_ollama_with_context :: '+str(response_list))
    return response_list
            

"""
Common
"""
def build_request_data(query: str, chunk: str="", api_type: str="generate"):
    data = {
        'model': choose_model(query, chunk, api_type),
        'options': {}
    }
    if api_type == 'generate':
        data['prompt'] = f"{query} ``` {chunk} ```"
        data['stream'] = False
        data['format'] = 'json'
    elif api_type == 'chat':
        data['messages'] = f"{query} ``` {chunk} ```"
        data['stream'] = False
        data['format'] = 'json'
    elif api_type == 'embeddings':
        data['prompt'] = query
    return data

def send_post_request(api_url, data):
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Error during API call: {e}")
        return None

def parse_response(response, api_type):
    if api_type == 'chat':
        return unmark(response.json().get('message', {}).get('content', ''))
        #return unmark(response.json().get('message', {}).get('content', '')).replace('\n', ' ')
    elif api_type == 'generate':
        return unmark(response.json().get('response', ''))
        #return unmark(response.json().get('response', '')).replace('\n', ' ')
    # 다른 API 유형에 대한 처리는 여기에 추가

def choose_model(query, context, api_type):
    return 'gemma:latest'

def chunking_context(context):
    context_chunks = []
    for index in range(len(context) // CHUNK_SIZE + 1):
        start_index = max(0, index * CHUNK_SIZE - OVERLAP_SIZE)
        end_index = (index + 1) * CHUNK_SIZE
        context_chunks.append(context[start_index:end_index])
    return context_chunks
