import requests
from common.text import unmark
import json
import time
from tqdm import tqdm
import traceback
import ast
import ray
from ray.util.multiprocessing import Pool
from common.constants import Constants
import wandb
import threading
from typing import Tuple

CHUNK_SIZE = 1024
OVERLAP_SIZE = 200

API_URLS = {
    'chat'      : 'http://localhost:11434/api/chat',
    'generate'  : 'http://localhost:11434/api/generate',
    'embeddings': 'http://localhost:11434/api/embeddings',
    # 추가 엔드포인트가 생길 경우 여기에 추가
    # 'another_api': 'http://localhost:11434/api/another'
}

constants = Constants.get_instance()

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
    data = build_request_data(query=text, chunk='', options={'api_type':'embeddings'})
    response = send_post_request(api_url, data)
    #print(response.json())
    #print(text)
    return response.json()['embedding']


"""
Query (chat, completion, instruct, generate, etc)
"""
def query_with_context(query:str, title: str, context:str, options: dict = {'api_type':'generate', 
                                                                'chunk_size':CHUNK_SIZE,
                                                                'format':'json'}) -> list[dict]:
    response_list = query_ollama_with_context(query, title, context, options=options)
    return response_list
#   query_ollama_with_context(query, context, api_type='chat')
#   query_ollama_with_context(query, context, api_type='another_api')


def query_ollama_with_context(query:str, title:str, context:str, options:dict) -> list[dict]:
    if options['api_type'] not in API_URLS:
        raise ValueError(f"Unsupported API type: {options['api_type']}")
    
    api_url = API_URLS[options['api_type']]
    context_chunks = chunking_context(context, options['chunk_size'])
    response_list = []
    
    response_list = []
    ray.init()
    with Pool() as pool:
        results = pool.map(lambda chunk: process_chunk(chunk, query, title, options, api_url), context_chunks)
        for result in results:
            if result is not None:
                response_list.append(result)

    return response_list

def process_chunk(chunk, query, title, options, api_url):
    if (len(chunk) < 20):
        return None

    data = build_request_data(query, f"{title}\n\n{chunk}", options)
    begin = time.time()
    thread_count_before = threading.active_count()
    response, thread_count_during = send_post_request(api_url, data)
    end = time.time()
    thread_count_after = threading.active_count()
    wandb.log({'chunk_size':len(chunk), 
               'elapsed_time':end - begin, 
               'thread_count_before':thread_count_before,
               'thread_count_during':thread_count_during,
               'thread_count_after':thread_count_after})
    print(f"query_ollama_with_context elapsed time (chunk {len(chunk)}) : {end - begin}")
    try:
        if response:
            if options['format'] == 'json':
                ascii_contents = parse_response(response, options['api_type'])
                ascii_contents = json.loads(json.dumps(ast.literal_eval(ascii_contents)))
            else:
                ascii_contents = parse_response(response, options['api_type'])

            return ascii_contents
    except Exception as e:
        print(f"Error during response parsing: {e}")
        return None    

"""
Common
"""
def build_request_data(query:str, chunk:str, options:dict):
    data = {
        'model': choose_model(query, chunk, options['api_type']),
        'options': {}
    }
    if options['api_type'] == 'generate':
        data['prompt'] = f"{query} ``` {chunk} ```"
        data['stream'] = False
        if options['format'] is not None: 
            data['format'] = options['format']
    elif options['api_type'] == 'chat':
        data['messages'] = f"{query} ``` {chunk} ```"
        data['stream'] = False
        if options['format'] is not None: 
            data['format'] = options['format']
    elif options['api_type'] == 'embeddings':
        data['prompt'] = query
    return data

def send_post_request(api_url:str, data:str) -> Tuple[requests.Response, int]:
    try:
        response = requests.post(api_url, json=data)
        thread_count_during = threading.active_count()
        response.raise_for_status()
        return response, thread_count_during
    except requests.RequestException as e:
        print(f"Error during API call: {e}")
        return None, None

def parse_response(response:str, api_type:str):
    if api_type == 'chat':
        return unmark(response.json().get('message', {}).get('content', ''))
    elif api_type == 'generate':
        return unmark(response.json().get('response', ''))

def choose_model(query:str, context:str, api_type:str):
    return 'gemma2:9b-instruct-q2_K'

def chunking_context(context:str, chunk_size:int):
    context_chunks = []
    for index in range(len(context) // chunk_size + 1):
        start_index = max(0, index * chunk_size - OVERLAP_SIZE)
        end_index = (index + 1) * chunk_size
        context_chunks.append(context[start_index:end_index])
    return context_chunks
