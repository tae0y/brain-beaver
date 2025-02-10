import pika
import json
from common.datasources.markdown import Markdown
from common.llmroute.llmrouter import LLMRouter

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
        if datasourcetype == 'markdown':
            Markdownloader = Markdown(datasourcepath)
            lazy_list = Markdownloader.get_lazy_list(
                shuffle_flag=True,
                ignore_dir_list=options['ignore_dir_list'],
            )

        reasoning_sum = 0
        embedding_sum = 0
        openai_reasoning_client = self.llmclients['gpt-4o-mini']
        openai_embedding_client = self.llmclients['text-embedding-3-small']

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
            except Exception as e:
                print(f"\nLOG-ERROR: error reading {filepath} - {str(e)}")

        print(f"\nLOG-DEBUG: OpenAI processing {num} files costs (KRW) :\t reasoning {round(reasoning_sum,2)}, embedding {round(embedding_sum,2)}")


        pass

    def extract(self, datasourcetype: str, datasourcepath: str, options: dict):
        """
        데이터소스로부터 주요개념을 추출한다
        """
        pass


    # --------------------------------------------------------------
    # RABBITMQ
    def publish_extracted_dataloader(self, options):
        """
        """

        with pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            message = []
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            connection.close()

        pass