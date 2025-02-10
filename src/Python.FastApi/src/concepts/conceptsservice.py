import datetime
import pika
import json
from typing import Tuple
from common.datasources.markdown import Markdown
from concepts.conceptsreposigory import ConceptsRepository
#from networks.networksservice import NetworksService #순환참조 발생으로 각주처리
from llmroute.llmrouter import LLMRouter
from llmroute.baseclient import BaseClient
from llmroute.openaiclient import OpenAIClient
from llmroute.ollamaclient import OllamaClient

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'extract_dataloader_queue'

class ConceptsService:
    repository : ConceptsRepository
    llmclients : dict
    #networkService : NetworksService 

    def __init__(self):
        self.repository = ConceptsRepository()
        #self.networkService = NetworksService()
        self.start_consumer()

        llmrouter = LLMRouter()
        self.llmclients = llmrouter.get_clients_all()
        pass

    # ---------------------------------------------------
    # BASE CRUD
    def create_concepts(self, concepts_list: list[dict]) -> dict:
        self.repository.create_tb_concepts_list(concepts_list)
        return {"status": "success"}

    def update_concepts(self, concepts_list: list[dict]) -> dict:
        self.repository.update_tb_concepts_list(concepts_list)
        return {"status": "success"}

    def get_concepts(self) -> dict:
        concept_list = self.repository.read_tb_concepts_all()
        return {"status": "success", "data": concept_list}

    def get_concept(self, concept_id: int) -> dict:
        concept = self.repository.read_tb_concepts(concept_id)
        return {"status": "success", "data": concept}

    def get_concepts_count(self) -> dict:
        count = self.repository.read_tb_concepts_count()
        return {"status": "success", "data": count}

    # ---------------------------------------------------
    # RABBITMQ
    def callback(self, channel, method, properties, body):
        concepts = json.loads(body)
        for concept in concepts:
            self.create_concepts(concept)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start_consumer(self):
        with pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.callback)
            channel.start_consuming()

    # ---------------------------------------------------
    def get_markdown_lazy_list(self, datasourcepath: str) -> list:
        MarkdownLoader = Markdown(datasourcepath)
        lazy_list = MarkdownLoader.get_lazy_list(
                                                    shuffle_flag=True, 
                                                    ignore_dir_list=None
                                                )
        return lazy_list


    def assume_total_cost(self, lazy_list: list, options: dict) -> float:
        reasoning_sum = 0
        embedding_sum = 0
        openai_reasoning_client = self.llmclients['gpt-4o-mini']
        openai_embedding_client = self.llmclients['text-embedding-3-small']
        #ollama_gemma_client = self.llmclients['gemma2:9b-instruct-q5_K_M']

        if 'max_file_num' in options:
            num = options['max_file_num']
        else:
            num = len(lazy_list)
        for filepath, loader_func in lazy_list[:num]: #TEST: 3개만 처리
            try:
                data = loader_func()
                reasoning_cost = openai_reasoning_client.get_how_much_cost(data)
                embedding_cost = openai_embedding_client.get_how_much_cost(data)
                reasoning_sum += reasoning_cost
                embedding_sum += embedding_cost

                #print(f"\nLOG-DEBUG: {filepath} - {len(data)}")
                #print(f"\nLOG-DEBUG: text_length {len(data)}\t reasoning_cost {round(reasoning_cost,2)}\t embedding_cost {round(embedding_cost,2)}\t reasoning_sum {round(reasoning_sum,2)}\t embedding_sum {round(embedding_sum,2)}")
                #data_list.append(data)
            except Exception as e:
                print(f"\nLOG-ERROR: error reading {filepath} - {str(e)}")

        print(f"\nLOG-DEBUG: OpenAI processing {num} files costs (KRW) :\t reasoning {round(reasoning_sum,2)}, embedding {round(embedding_sum,2)}")
        return reasoning_sum + embedding_sum


    def extract_keyconcepts(self, data_name: str, data_loader: callable, options: dict) -> list:
        """
        주요개념 추출 및 DB 저장
        TODO: 메서드가 단일 책임을 져야한다면.. 추출/임베딩/DB저장 메서드를 분리해야할까?
        TODO: OpenAI는 추론, 임베딩 모델의 종류가 다르니, 옵션으로 구분해서 받을 수 있도록 수정
        """
        reason_model_client : BaseClient
        embed_model_client : BaseClient
        prompt : str
        format : dict


        # 변수 설정
        data = data_loader()
        if data is None or len(data) == 0:
            return

        reason_model_client = self.llmclients[options['model_name']] if 'model_name' in options else self.llmclients['gemma2:9b-instruct-q5_K_M']
        embed_model_client = self.llmclients[options['model_name']] if 'model_name' in options else self.llmclients['gemma2:9b-instruct-q5_K_M']
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

        # 추출
        data_extracted = []
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
            data_extracted.append(response.data)
            print(f"\nLOG-DEBUG: {i} - {response.data}")

        # 임베딩
        batch_size : int
        max_embedding_size = 4096
        if isinstance(embed_model_client, OpenAIClient):
            batch_size = 1
        elif isinstance(embed_model_client, OllamaClient):
            batch_size = 10
        for i in range(0, len(data_extracted), batch_size):
            batch = data_extracted[i:i+batch_size]
            texts_to_embed = [f"{data.get('title','')} {data.get('summary','')}" for data in batch]
            embeddings = embed_model_client.embed(texts_to_embed, {}, 'batch').data

            for extracted, embedding in zip(batch, embeddings):
                extracted['embedding']   = self.pad_embedding_with_zero_until_4096(embedding)
                extracted['status']      = None
                extracted['data_name']   = data_name
                extracted['create_time'] = datetime.datetime.now()
                extracted['update_time'] = None
                extracted['source_num']  = 0
                extracted['target_num']  = 0

        # 저장
        self.repository.create_tb_concepts_list(data_extracted)


    def pad_embedding_with_zero_until_4096(self, embedding: list) -> list:
        """
        4096차원으로 패딩
        TODO: 모델 Client 쪽으로 로직을 이동할까?
        """
        return embedding + [0.0] * (4096 - len(embedding))

    def read_concepts_all(self):
        return self.repository.read_tb_concepts_all()

    def read_concepts_nearest_by_embedding(self, source, operation, limit):
        return self.repository.read_tb_concepts_nearest_by_embedding(source, operation, limit)

    def update_concepts_source_target_count(self):
        from networks.networksservice import NetworksService
        networkService = NetworksService()
        networks_list = networkService.read_networks_all()

        source_count_dict = {}
        target_count_dict = {}
        for network in networks_list:
            source_count_dict[network.source_concept_id] = source_count_dict.get(network.source_concept_id, 0) + 1
            target_count_dict[network.target_concept_id] = target_count_dict.get(network.target_concept_id, 0) + 1

        concept_id_list = source_count_dict.keys() | target_count_dict.keys()
        for id in concept_id_list:
            self.repository.update_tb_concepts_source_target_count(id, source_count_dict.get(id, 0), target_count_dict.get(id, 0))

    def get_concepts_all_count(self) -> int:
        return len(self.repository.read_tb_concepts_all_idonly())

    def read_concepts_top(self, limit: int) -> list:
        return self.repository.read_tb_concepts_top(limit)