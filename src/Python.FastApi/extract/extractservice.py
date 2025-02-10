import pika
import json
import traceback
import datetime
from common.datasources.markdown import Markdown
from common.llmroute.llmrouter import LLMRouter
from common.llmroute.openaiclient import OpenAIClient
from common.llmroute.ollamaclient import OllamaClient
from common.llmroute.baseclient import BaseClient
from concepts.conceptsmodel import Concepts


RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'extract_dataloader_queue'


class ExtractService:
    def __init__(self):
        llmrouter = LLMRouter()
        self.llmclients = llmrouter.get_clients_all()
        pass


    # --------------------------------------------------------------
    # BASE LOGIC
    def check_budget(self, datasourcetype: str, datasourcepath: str, options: dict):
        """
        데이터소스로부터 데이터를 읽고 예산을 추정한다.
        """
        # prepare
        reason_model_client : BaseClient
        embed_model_client : BaseClient
        reasoning_sum = 0
        embedding_sum = 0

        # process
        status = 'success'
        data = ''
        try:
            # load data lazy list
            shuffle_flag = options['shuffle_flag'] if 'shuffle_flag' in options else False
            if datasourcetype == 'markdown':
                Markdownloader = Markdown(datasourcepath)
                lazy_list = Markdownloader.get_lazy_list(
                    shuffle_flag=shuffle_flag,
                    ignore_dir_list=options['ignore_dir_list'],
                )

            # estimate cost
            reason_model_name = options['reason_model_name'] if 'reason_model_name' in options else 'gemma2:9b-instruct-q5_K_M'
            embed_model_name = options['embed_model_name'] if 'embed_model_name' in options else 'gemma2:9b-instruct-q5_K_M'
            reason_model_client = self.llmclients[reason_model_name]
            embed_model_client = self.llmclients[embed_model_name]
            if isinstance(reason_model_client, OllamaClient):
                print(f"\nLOG-INFO: reasoning with OllamaClient is free!! Fell free to use it.")
            if isinstance(embed_model_client, OllamaClient):
                print(f"\nLOG-INFO: embedding with OllamaClient is free!! Fell free to use it.")

            max_data_num = options['max_file_num'] if 'max_file_num' in options else len(lazy_list)
            for filepath, loader_func in lazy_list[:max_data_num]:
                try:
                    data = loader_func()
                    reasoning_cost = reason_model_client.get_how_much_cost(data)
                    embedding_cost = embed_model_client.get_how_much_cost(data)
                    reasoning_sum += reasoning_cost
                    embedding_sum += embedding_cost
                except Exception as e:
                    print(f"\nLOG-ERROR: error reading {filepath} - {str(e)}")
            reasoning_cost *= 2 # for output token
            embedding_cost *= 2

            status = 'success'
            data = {
                'reasoning_sum': reasoning_sum,
                'embedding_sum': embedding_sum
            }
        except Exception as e:
            print(f"\nLOG-ERROR: error reading {datasourcetype}, {datasourcepath} - {str(e)}")
            traceback.print_exc()

            status = 'error'
            data = str(e)


        # return
        return {
            'status': status,
            'data': data
        }


    def extract(self, datasourcetype: str, datasourcepath: str, options: dict):
        """
        데이터소스로부터 주요개념을 추출한다
        """
        # prepare
        status = 'success'
        data = ''

        # process
        try:
            # load data lazy list
            shuffle_flag = options['shuffle_flag'] if 'shuffle_flag' in options else False
            if datasourcetype == 'markdown':
                Markdownloader = Markdown(datasourcepath)
                lazy_list = Markdownloader.get_lazy_list(
                    shuffle_flag=shuffle_flag,
                    ignore_dir_list=options['ignore_dir_list'],
                )

            max_data_num = options['max_file_num'] if 'max_file_num' in options else len(lazy_list)
            reason_model_name = options['reason_model_name']
            embed_model_name = options['embed_model_name']
            for data_name, data_loader in lazy_list[:max_data_num]: # TODO: 프로그레스바 추가
                try:
                    print(f"\nLOG-INFO: extracting {data_name}")

                    # extract keyconcepts from data
                    concepts_list = self.extract_keyconcepts_from_data(
                        data_name, 
                        data_loader, 
                        {
                            'reason_model_name' : reason_model_name,
                            'embed_model_name' : embed_model_name
                        })

                    # publish message to rabbitmq
                    if not concepts_list and len(concepts_list) > 0:
                        self.publish_extracted_dataloader(concepts_list)

                except Exception as e:
                    print(f"\nLOG-ERROR: error reading {data_name} - {str(e)}")


            status = 'success'
            data = ''

        except Exception as e:
            print(f"\nLOG-ERROR: error reading {datasourcetype}, {datasourcepath} - {str(e)}")
            traceback.print_exc()

            status = 'error'
            data = str(e)


        # return
        return {
            'status': status,
            'data': data
        }
        pass

    def extract_keyconcepts_from_data(self, data_name:str, data_loader:callable, options:dict) -> list[dict]:
        """
        """
        # prepare
        reason_model_client : BaseClient
        embed_model_client : BaseClient
        prompt : str
        format : dict
        reason_model_name = options['reason_model_name']
        embed_model_name = options['embed_model_name']
        reason_client = self.llmclients[reason_model_name]
        embed_client = self.llmclients[embed_model_name]

        status = ''
        data = []

        # process
        try:
            # set data, llmclients, prompt, format
            data = data_loader()
            if not data:
                return []

            reason_model_client = self.llmclients[reason_model_name]
            embed_model_client = self.llmclients[embed_model_name]
            prompt = options['prompt'] if 'prompt' in options else """
            당신은 문서 요약의 대가입니다.

            다음 제시된 [DOCUMENT]는 소프트웨어 개발자가 개인적으로 학습한 내용을 정리한 마크다운 문서입니다.
            학습한 지식을 복습하고 확장할 수 있도록, 주요 내용을 추출하여 정리하고자 합니다.
            다음 제시된 문서의 내용을 기준으로, 주어진 기준과 형식에 맞춰 답변을 생성해주세요.

            1. title : 명사형으로 끝나는 한 문장 제목
            2. keywords : 다섯 개 이내의 명사형 키워드
            3. category : information, sentiment, question, insight 중에서 의미상 가장 가까운 카테고리를 하나만 선택
            4. summary : 주요 내용을 한 문단 이내로 요약하여 작성

            [DOCUMENT]
            """

            if 'format' in options:
                format = options['format']
            else:
                format_headless = {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "description": "title of the document in one sentence with a noun ending",
                                    "type": "string"
                                },
                                "keywords": {
                                    "description": "up to five noun keywords",
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "maxItems": 5
                                },
                                "category": {
                                    "description": "select one category from information, sentiment, question, insight",
                                    "type": "string",
                                    "enum": ["information", "sentiment", "question", "insight"]
                                },
                                "summary": {
                                    "description": "write a summary in one paragraph",
                                    "type": "string"
                                },
                            },
                            "required": ["title", "keywords", "category", "summary"],
                            "additionalProperties": False
                        }
                format_full = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response_schema",
                        "schema": format_headless
                    }
                }
                if isinstance(reason_model_client, OpenAIClient):
                    format = format_full
                elif isinstance(reason_model_client, OllamaClient):
                    format = format_headless


            # generate
            concepts_list = []
            data_size = len(data)
            chunk_size =  reason_model_client.get_chunk_size()
            chunk_count = data_size // chunk_size
            for i in range(0, chunk_count+1):
                chunk = data[i*chunk_size:(i+1)*chunk_size]
                response = reason_model_client.generate(
                    prompt = f"{prompt} data_name : {data_name}\n {chunk}",
                    options = {
                        "format" : format
                    }
                )
                concepts_list.append(response.data)
                print(f"\nLOG-DEBUG: {i} - {response.data}")

            # embed
            batch_size : int
            if isinstance(embed_model_client, OpenAIClient):
                batch_size = 1
            elif isinstance(embed_model_client, OllamaClient):
                batch_size = 10
            for i in range(0, len(concepts_list), batch_size):
                batch = concepts_list[i:i+batch_size]
                texts_to_embed = [f"{data.get('title','')} {data.get('summary','')}" for data in batch]
                embeddings = embed_model_client.embed(texts_to_embed, {}, 'batch').data

                for concept, embedding in zip(batch, embeddings):
                    concept['embedding']   = self.pad_embedding_with_zero_until_4096(embedding)
                    concept['status']      = None
                    concept['data_name']   = data_name
                    concept['create_time'] = datetime.datetime.now()
                    concept['update_time'] = None
                    concept['source_num']  = 0
                    concept['target_num']  = 0

            status = 'success'
            data = concepts_list

        except Exception as e:
            print(f"\nLOG-ERROR: error reading {data_name} - {str(e)}")
            traceback.print_exc()

            status = 'error'
            data = str(e)

        # return
        return {
            'status': status,
            'data': data
        }

    def pad_embedding_with_zero_until_4096(self, embedding: list[float]) -> list[float]:
        """
        임베딩 벡터를 4096차원으로 패딩한다.
        """
        return embedding + [0.0] * (4096 - len(embedding))


    # --------------------------------------------------------------
    # RABBITMQ
    def publish_extracted_dataloader(self, concepts_list:list[dict]):
        """
        """

        with pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            message = json.dumps(concepts_list)
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            connection.close()

        pass