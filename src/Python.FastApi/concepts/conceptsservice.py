import datetime
import pika
import json
import logging
from typing import Tuple
from common.datasources.markdown import Markdown
from concepts.conceptsreposigory import ConceptsRepository
#from networks.networksservice import NetworksService #순환참조 발생으로 각주처리

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'extract_dataloader_queue'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConceptsService:
    repository : ConceptsRepository
    llmclients : dict

    def __init__(self):
        self.repository = ConceptsRepository()
        self.start_consumer()
        pass

    # ---------------------------------------------------
    # BASE CRUD
    def create_concepts(self, concepts_list: list[dict]) -> dict:
        self.repository.create_tb_concepts_list(concepts_list)
        return {"status": "success"}

    def update_concepts(self, concepts_list: list[dict]) -> dict:
        raise NotImplementedError
        #self.repository.update_tb_concepts_list(concepts_list)
        #return {"status": "success"}

    def update_concepts_source_target_count(self, concept_id: int, source_num: int, target_num: int) -> dict:
        self.repository.update_tb_concepts_source_target_count(concept_id, source_num, target_num)
        return {"status": "success"}

    def get_concepts(self) -> dict:
        concept_list = self.repository.read_tb_concepts_all()
        return {"status": "success", "data": concept_list}

    def get_concept(self, concept_id: int) -> dict:
        concept = self.repository.read_tb_concepts_by_id(concept_id)
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
        logger.info("callback end")

    def start_consumer(self):
        logger.info("start_consumer called")
        with pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.callback)
            channel.start_consuming()
            logger.info("start_consumer ongoing")