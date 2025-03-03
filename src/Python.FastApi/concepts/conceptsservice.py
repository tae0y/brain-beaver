import datetime
import pika
import json
import logging
import threading
import time
from typing import Tuple
from common.datasources.markdown import Markdown
from concepts.conceptsreposigory import ConceptsRepository
from common.system.constants import Constants
#from networks.networksservice import NetworksService #순환참조 발생으로 각주처리

RABBITMQ_HOST = 'bws_mq'
QUEUE_NAME = 'extract_dataloader_queue'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConceptsService:
    repository : ConceptsRepository
    llmclients : dict

    def __init__(self):
        self.repository = ConceptsRepository()
        self.constants = Constants.get_instance()
        threading.Thread(target=self.start_consumer_retry, daemon=True).start() # 별도스레드에서 실행
        pass

    # ---------------------------------------------------
    # BASE CRUD
    def create_concepts(self, concepts_list: list[dict]) -> dict:
        status = ''
        data = ''
        try:
            for concept in concepts_list:
                concept['embedding'] = self.pad_vector_to4096(concept['embedding'])
            self.repository.create_tb_concepts_list(concepts_list)
            status = 'success'
            data = 'data created'
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def update_concepts(self, concepts: dict) -> dict:
        status = ''
        data = ''
        try:
            concepts['embedding'] = self.pad_vector_to4096(concepts['embedding'])
            self.repository.update_tb_concepts(concepts)
            status = 'success'
            data = 'data updated'
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def update_concepts_source_target_count(self, concept_id: int, source_num: int, target_num: int) -> dict:
        status = ''
        data = ''
        try:
            self.repository.update_tb_concepts_source_target_count(concept_id, source_num, target_num)
            status = 'success'
            data = 'data updated'
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def get_concepts(self) -> dict:
        status = ''
        data = ''
        try:
            concept_list = self.repository.read_tb_concepts_all()
            status = 'success'
            data = concept_list
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def get_concept(self, concept_id: int) -> dict:
        status = ''
        data = ''
        try:
            concept = self.repository.read_tb_concepts_by_id(concept_id)
            status = 'success'
            data = concept
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def get_concepts_count(self) -> dict:
        status = ''
        data = ''
        try:
            count = self.repository.read_tb_concepts_count()
            status = 'success'
            data = count
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def read_concepts_nearest_by_embedding(self, concept: dict, operation: str, topn: int) -> list:
        status = ''
        data = ''
        try:
            nearest_list = self.repository.read_tb_concepts_nearest_by_embedding(concept, operation, topn)
            status = 'success'
            data = nearest_list
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    def read_concpets_top_by_source_target_num(self, topn: int) -> list:
        status = ''
        data = ''
        try:
            top_list = self.repository.read_tb_concepts_top_by_source_target_num(topn)
            status = 'success'
            data = top_list
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}
    
    def delete_concepts_all(self) -> dict:
        status = ''
        data = ''
        try:
            self.repository.delete_tb_concepts_all()
            status = 'success'
            data = 'data deleted'
        except Exception as e:
            status = 'error'
            data = str(e)

        return {"status": status, "data": data}

    # ---------------------------------------------------
    # RABBITMQ
    def callback(self, channel, method, properties, body):
        concepts = json.loads(body)
        self.create_concepts(concepts)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start_consumer(self):
        credentials = pika.PlainCredentials(self.constants.rabbitmq_user, self.constants.rabbitmq_passwd)
        connection_params = pika.ConnectionParameters(RABBITMQ_HOST, credentials=credentials)
        with pika.BlockingConnection(connection_params) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.callback)
            channel.start_consuming()

    def start_consumer_retry(self):
        retry_max_num = 10
        retry_index = 0
        while retry_index < retry_max_num:
            try:
                self.start_consumer()
                logger.iinfo("message queue connection success")
            except Exception as e:
                logger.error(f"start_consumer error: {str(e)}")
                retry_index += 1
                logger.info(f"message queue connection failed. retry after 10 seconds... ({retry_index}/{retry_max_num}) ")
                time.sleep(10)

    # ---------------------------------------------------
    def pad_vector_to4096(self, vector: list) -> list:
        return vector + [0] * (4096 - len(vector))